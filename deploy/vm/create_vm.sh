#!/usr/bin/env bash
# Create the single free-tier VM that hosts ClickHouse + the official mcp-clickhouse server.
#
# Free tier (GCP "Always Free"): 1x e2-micro/month in us-west1, us-central1 or us-east1,
# 30 GB-months pd-standard, 1 GB network egress. We use exactly one of each.
# Idempotent: re-running only creates what is missing.
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-a}"          # fall back to -b if -a has no e2-micro capacity
VM="${VM:-slateiq-data}"
TAG="${TAG:-slateiq-data}"
DISK_GB="${DISK_GB:-30}"

echo "project=$PROJECT zone=$ZONE vm=$VM"

# ---------------------------------------------------------------- APIs
gcloud services enable compute.googleapis.com --project "$PROJECT" --quiet >/dev/null

# ---------------------------------------------------------------- firewall
# Public surface is TLS only: 80 (ACME HTTP-01 + redirect), 443, 8443 (alt TLS).
# ClickHouse 8123/9000 are bound to 127.0.0.1 on the VM and are never exposed.
if ! gcloud compute firewall-rules describe slateiq-allow-web --project "$PROJECT" >/dev/null 2>&1; then
  gcloud compute firewall-rules create slateiq-allow-web \
    --project "$PROJECT" --network default --direction INGRESS --priority 1000 \
    --action ALLOW --rules tcp:80,tcp:443,tcp:8443,udp:443 \
    --source-ranges 0.0.0.0/0 --target-tags "$TAG" \
    --description "SlateIQ: Caddy TLS edge (ACME + MCP + ClickHouse proxy)" --quiet
else
  echo "firewall slateiq-allow-web already exists"
fi

# ---------------------------------------------------------------- instance
if gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" >/dev/null 2>&1; then
  echo "instance $VM already exists in $ZONE"
  # Converge the startup-script even on an existing box: bootstrap.sh is what installs and
  # enables slateiq-stack.service, so an edit to it must reach a VM that was created earlier.
  # (Metadata is only read at boot; run `sudo google_metadata_script_runner startup` on the VM,
  # or just reboot, to apply it now.)
  echo "--- refreshing startup-script metadata from bootstrap.sh"
  gcloud compute instances add-metadata "$VM" --zone "$ZONE" --project "$PROJECT" \
    --metadata-from-file startup-script=bootstrap.sh --quiet >/dev/null
else
  gcloud compute instances create "$VM" \
    --project "$PROJECT" \
    --zone "$ZONE" \
    --machine-type e2-micro \
    --image-family debian-12 --image-project debian-cloud \
    --boot-disk-size "${DISK_GB}GB" --boot-disk-type pd-standard --boot-disk-device-name "$VM" \
    --tags "$TAG" \
    --network-interface "network=default,subnet=default,stack-type=IPV4_ONLY" \
    --no-service-account --no-scopes \
    --metadata-from-file startup-script=bootstrap.sh \
    --metadata google-logging-enabled=false,google-monitoring-enabled=false,enable-osconfig=FALSE,serial-port-logging-enable=TRUE \
    --maintenance-policy MIGRATE \
    --deletion-protection \
    --labels app=slateiq,tier=data,cost=free \
    --quiet
fi
# Notes on the flags above:
#   --no-service-account/--no-scopes : nothing on the VM calls Google APIs, so it gets no identity.
#   google-logging/monitoring=false  : keeps the Ops Agent off (RAM) and Cloud Logging ingest at zero.
#   --deletion-protection            : this box holds the demo dataset; require an explicit unset to delete.

IP=$(gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo
echo "VM_NAME=$VM"
echo "VM_ZONE=$ZONE"
echo "VM_IP=$IP"
echo "PUBLIC_HOST=${IP}.sslip.io"
echo
echo "Next: ./deploy_stack.sh   (copies compose/ up, writes .env, brings the stack online)"
