#!/usr/bin/env bash
# Push compose/ to the VM, generate/reuse secrets, and bring ClickHouse + mcp-clickhouse + Caddy up.
# Idempotent. Safe to re-run after editing anything under deploy/vm/compose/.
set -euo pipefail
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
ZONE="${ZONE:-us-central1-a}"
VM="${VM:-slateiq-data}"
SECRETS="$REPO_ROOT/.secrets/deploy.env"
STACK_DIR=/opt/slateiq

gssh() { gcloud compute ssh "$VM" --zone "$ZONE" --project "$PROJECT" --quiet --command "$1" < /dev/null; }

IP=$(gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" \
      --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
[ -n "$IP" ] || { echo "no external IP for $VM"; exit 1; }
PUBLIC_HOST="${IP}.sslip.io"
echo "VM=$VM IP=$IP PUBLIC_HOST=$PUBLIC_HOST"

# ---------------------------------------------------------------- secrets (generated once, gitignored)
mkdir -p "$REPO_ROOT/.secrets"
if [ ! -f "$SECRETS" ]; then
  echo "--- generating $SECRETS"
  umask 077
  cat > "$SECRETS" <<SEC
# SlateIQ deploy secrets — GITIGNORED, never commit.
CH_DEFAULT_PASSWORD=$(openssl rand -hex 24)
CH_AGENT_RO_PASSWORD=$(openssl rand -hex 24)
CLICKHOUSE_MCP_TOKEN=$(openssl rand -hex 32)
SEC
fi
# shellcheck disable=SC1090
set -a; . "$SECRETS"; set +a

# Refresh the derived (non-secret) values on every run — the IP can change on stop/start.
python3 - "$SECRETS" "$PUBLIC_HOST" <<'PY'
import sys, re
path, host = sys.argv[1], sys.argv[2]
lines = [l for l in open(path).read().splitlines()
         if not re.match(r'^(PUBLIC_HOST|CLICKHOUSE_MCP_URL|CLICKHOUSE_HTTP_URL)=', l)]
lines += [f"PUBLIC_HOST={host}",
          f"CLICKHOUSE_MCP_URL=https://{host}/mcp",
          f"CLICKHOUSE_HTTP_URL=https://{host}/ch"]
open(path, "w").write("\n".join(lines) + "\n")
PY
set -a; . "$SECRETS"; set +a

# ---------------------------------------------------------------- wait for bootstrap
echo "--- waiting for startup-script (docker) to finish"
for i in $(seq 1 40); do
  if gssh 'test -f /var/run/slateiq-bootstrap-done && docker --version' >/dev/null 2>&1; then
    echo "    bootstrap done"; break
  fi
  echo "    ...$i"; sleep 15
done
gssh 'docker --version && docker compose version && free -m'

# ---------------------------------------------------------------- ship the bundle
echo "--- copying compose bundle"
gssh "sudo mkdir -p $STACK_DIR && sudo chown -R \$(id -u):\$(id -g) $STACK_DIR"
tar czf /tmp/slateiq-compose.tgz -C compose .
gcloud compute scp /tmp/slateiq-compose.tgz "$VM":/tmp/slateiq-compose.tgz \
  --zone "$ZONE" --project "$PROJECT" --quiet
gssh "tar xzf /tmp/slateiq-compose.tgz -C $STACK_DIR && rm -f /tmp/slateiq-compose.tgz && mkdir -p $STACK_DIR/seed"

# ---------------------------------------------------------------- .env on the VM (0600, root-owned)
echo "--- writing $STACK_DIR/.env"
gssh "umask 077; cat > $STACK_DIR/.env <<'VMENV'
PUBLIC_HOST=$PUBLIC_HOST
CH_DEFAULT_PASSWORD=$CH_DEFAULT_PASSWORD
CH_AGENT_RO_PASSWORD=$CH_AGENT_RO_PASSWORD
CLICKHOUSE_MCP_TOKEN=$CLICKHOUSE_MCP_TOKEN
CH_PROXY_USER=agent_ro
VMENV
chmod 600 $STACK_DIR/.env"

# ---------------------------------------------------------------- up
echo "--- docker compose up -d --build"
gssh "cd $STACK_DIR && docker compose up -d --build --remove-orphans"
gssh "cd $STACK_DIR && docker compose ps"

# ---------------------------------------------------------------- verify
echo "--- waiting for TLS + health (Let's Encrypt issuance takes ~30-60s on first boot)"
for i in $(seq 1 30); do
  if curl -fsS --max-time 10 "https://$PUBLIC_HOST/health" >/dev/null 2>&1; then break; fi
  echo "    ...$i"; sleep 10
done
echo -n "MCP  /health : "; curl -fsS --max-time 10 "https://$PUBLIC_HOST/health" || echo FAILED
echo -n "CH   /ch/ping: "; curl -fsS --max-time 10 "https://$PUBLIC_HOST/ch/ping" || echo FAILED
echo -n "CH   auth    : "; curl -fsS --max-time 15 "https://$PUBLIC_HOST/ch/" \
  --user "agent_ro:$CH_AGENT_RO_PASSWORD" --data-binary 'SELECT version()' || echo FAILED
echo -n "MCP  no token: "; curl -s -o /dev/null -w '%{http_code} (expect 401)\n' --max-time 10 -X POST "https://$PUBLIC_HOST/mcp"

cat <<OUT

Live endpoints
  CLICKHOUSE_MCP_URL   = https://$PUBLIC_HOST/mcp
  CLICKHOUSE_MCP_TOKEN = (see .secrets/deploy.env)
  ClickHouse HTTP      = https://$PUBLIC_HOST/ch/   (user agent_ro, read-only)
OUT
