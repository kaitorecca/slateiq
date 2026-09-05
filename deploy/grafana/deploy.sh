#!/usr/bin/env bash
# Deploy Grafana (OSS, anonymous Viewer, ClickHouse datasource) to Cloud Run.
#
# Free-tier shape: min-instances 0, max 1, 1 vCPU / 512 MiB. Grafana keeps its sqlite state
# in /tmp (tmpfs) — everything that matters is provisioned from the image, so a cold start
# rebuilds the exact same org, datasource and dashboard. Nothing is persisted, nothing costs.
set -euo pipefail
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-slateiq-grafana}"
AR_REPO="${AR_REPO:-slateiq}"
SECRET_NAME="${SECRET_NAME:-slateiq-ch-ro-password}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/grafana"
TAG="${TAG:-$(date -u +%Y%m%d-%H%M%S)}"

set -a; [ -f "$REPO_ROOT/.secrets/deploy.env" ] && . "$REPO_ROOT/.secrets/deploy.env"; set +a
: "${PUBLIC_HOST:?PUBLIC_HOST missing — run deploy/vm/deploy_stack.sh first}"
: "${CH_AGENT_RO_PASSWORD:?CH_AGENT_RO_PASSWORD missing — run deploy/vm/deploy_stack.sh first}"
CH_USER="${CH_USER:-agent_ro}"

echo "project=$PROJECT service=$SERVICE ch_host=$PUBLIC_HOST"

ENABLED=$(gcloud services list --enabled --project "$PROJECT" --format='value(config.name)')
MISSING=""
for api in run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com; do
  echo "$ENABLED" | grep -qx "$api" || MISSING="$MISSING $api"
done
# `gcloud services enable` takes minutes even when everything is already on, so only call it
# when something is genuinely missing.
[ -n "$MISSING" ] && gcloud services enable $MISSING --project "$PROJECT" --quiet >/dev/null

if ! gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$AR_REPO" --repository-format docker \
    --location "$REGION" --description "SlateIQ container images" --project "$PROJECT" --quiet
fi

# ---------------------------------------------------------------- secret: read-only CH password
if ! gcloud secrets describe "$SECRET_NAME" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud secrets create "$SECRET_NAME" --replication-policy=user-managed --locations="$REGION" \
    --labels=app=slateiq --project "$PROJECT" --quiet
fi
CUR=$(gcloud secrets versions access latest --secret "$SECRET_NAME" --project "$PROJECT" 2>/dev/null || true)
if [ "$CUR" != "$CH_AGENT_RO_PASSWORD" ]; then
  printf '%s' "$CH_AGENT_RO_PASSWORD" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project "$PROJECT" --quiet
  for v in $(gcloud secrets versions list "$SECRET_NAME" --filter='state:ENABLED' \
             --format='value(name)' --sort-by='~name' --project "$PROJECT" | tail -n +2); do
    gcloud secrets versions destroy "$v" --secret "$SECRET_NAME" --project "$PROJECT" --quiet || true
  done
fi
PNUM=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
# Runtime identity: prefer a real project SA (this project has no Compute Engine default SA),
# fall back to the compute default where one exists.
if [ -z "${RUNTIME_SA:-}" ]; then
  for cand in "slateiq-dev@${PROJECT}.iam.gserviceaccount.com" "${PNUM}-compute@developer.gserviceaccount.com"; do
    if gcloud iam service-accounts describe "$cand" --project "$PROJECT" >/dev/null 2>&1; then RUNTIME_SA="$cand"; break; fi
  done
fi
: "${RUNTIME_SA:?no usable runtime service account found}"
echo "runtime service account: $RUNTIME_SA"
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member "serviceAccount:${RUNTIME_SA}" --role roles/secretmanager.secretAccessor \
  --project "$PROJECT" --quiet >/dev/null

# ---------------------------------------------------------------- build + deploy
# This project has no Compute Engine default service account, so Cloud Build must be told
# which identity to run as, and logs must go to a user-owned regional bucket.
gcloud builds submit . --project "$PROJECT" --region "$REGION" \
  --tag "${IMAGE}:${TAG}" \
  --service-account="projects/${PROJECT}/serviceAccounts/${RUNTIME_SA}" \
  --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET --quiet

# Two-pass deploy: GF_SERVER_ROOT_URL must be the service's own URL, which we only know
# after the first deploy. Pass 1 creates it, pass 2 stamps the root URL in.
deploy() {   # $1 = root url (may be empty on the first pass)
  gcloud run deploy "$SERVICE" \
    --project "$PROJECT" --region "$REGION" \
    --image "${IMAGE}:${TAG}" \
    --platform managed --allow-unauthenticated \
    --min-instances 0 --max-instances 1 \
    --cpu 1 --memory 512Mi --concurrency 40 --timeout 300 \
    --port 8080 \
    --service-account "$RUNTIME_SA" \
    --labels app=slateiq,tier=grafana \
    --set-secrets "CH_PASSWORD=${SECRET_NAME}:latest" \
    --set-env-vars "^@^CH_HOST=${PUBLIC_HOST}@CH_USER=${CH_USER}@GF_SERVER_ROOT_URL=${1:-}@GF_SERVER_SERVE_FROM_SUB_PATH=false" \
    --quiet
}
deploy ""
URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format='value(status.url)')
deploy "$URL"

echo
echo "GRAFANA_URL=$URL"
echo -n "GET /api/health -> "; curl -fsS --max-time 60 "$URL/api/health" || echo FAILED
echo
echo -n "datasource health -> "
curl -fsS --max-time 60 "$URL/api/datasources/uid/slateiq-clickhouse" 2>/dev/null \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("type"), d.get("jsonData",{}).get("host"))' \
  || echo "(anonymous API read disabled or datasource not ready)"
echo "dashboard: $URL/d/slateiq-prod-health"
echo
echo "Add to .secrets/deploy.env and re-run deploy/cloudrun/deploy_agent.sh:  GRAFANA_URL=$URL"
