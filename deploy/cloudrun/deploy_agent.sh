#!/usr/bin/env bash
# Build + deploy the SlateIQ ADK agent (FastAPI) to Cloud Run.
#
# Free-tier shape: min-instances 0 (scale to zero = no idle cost), max 2, 1 vCPU / 1 GiB,
# concurrency 40. Cloud Run's always-free grant (2M requests, 180k vCPU-s, 360k GiB-s /month)
# comfortably covers a hackathon demo.
#
# Source of truth for config is .secrets/deploy.env (written by deploy/vm/deploy_stack.sh)
# plus .env for the Gemini key. GOOGLE_API_KEY is stored in Secret Manager and mounted as
# an env var, never baked into the image or passed on the command line.
set -euo pipefail
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-slateiq}"
AR_REPO="${AR_REPO:-slateiq}"
SECRET_NAME="${SECRET_NAME:-slateiq-google-api-key}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/${AR_REPO}/${SERVICE}"
TAG="${TAG:-$(date -u +%Y%m%d-%H%M%S)}"

echo "project=$PROJECT region=$REGION service=$SERVICE image=$IMAGE:$TAG"

# ---------------------------------------------------------------- config
set -a
[ -f "$REPO_ROOT/.env" ] && . "$REPO_ROOT/.env"
[ -f "$REPO_ROOT/.secrets/deploy.env" ] && . "$REPO_ROOT/.secrets/deploy.env"
set +a
: "${GOOGLE_API_KEY:?GOOGLE_API_KEY missing — put it in .env}"
CLICKHOUSE_MCP_URL="${CLICKHOUSE_MCP_URL:-}"
CLICKHOUSE_MCP_TOKEN="${CLICKHOUSE_MCP_TOKEN:-}"
CLIPS_BASE_URL="${CLIPS_BASE_URL:-}"
GRAFANA_URL="${GRAFANA_URL:-}"
[ -n "$CLICKHOUSE_MCP_URL" ] || echo "WARN: CLICKHOUSE_MCP_URL empty — run deploy/vm/deploy_stack.sh first"

# ---------------------------------------------------------------- APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com --project "$PROJECT" --quiet >/dev/null

# ---------------------------------------------------------------- Artifact Registry
if ! gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$AR_REPO" --repository-format docker \
    --location "$REGION" --description "SlateIQ container images" --project "$PROJECT" --quiet
  # Free tier is 0.5 GB storage: expire untagged images after 7 days so we stay under it.
  cat > /tmp/slateiq-ar-policy.json <<'POL'
[{"name":"delete-untagged","action":{"type":"Delete"},
  "condition":{"tagState":"untagged","olderThan":"7d"}},
 {"name":"keep-recent","action":{"type":"Keep"},"mostRecentVersions":{"keepCount":5}}]
POL
  gcloud artifacts repositories set-cleanup-policies "$AR_REPO" --location "$REGION" \
    --project "$PROJECT" --policy=/tmp/slateiq-ar-policy.json --no-dry-run --quiet || \
    echo "(cleanup policy skipped)"
else
  echo "artifact registry repo $AR_REPO already exists"
fi

# ---------------------------------------------------------------- Secret Manager
# Free tier: 6 active secret versions + 10k access ops/month. We keep exactly one version
# per secret and destroy older ones so the count never grows.
if ! gcloud secrets describe "$SECRET_NAME" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud secrets create "$SECRET_NAME" --replication-policy=user-managed --locations="$REGION" \
    --labels=app=slateiq --project "$PROJECT" --quiet
fi
CUR=$(gcloud secrets versions access latest --secret "$SECRET_NAME" --project "$PROJECT" 2>/dev/null || true)
if [ "$CUR" != "$GOOGLE_API_KEY" ]; then
  printf '%s' "$GOOGLE_API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project "$PROJECT" --quiet
  # Keep only the newest enabled version (free-tier version budget).
  for v in $(gcloud secrets versions list "$SECRET_NAME" --filter='state:ENABLED' \
             --format='value(name)' --sort-by='~name' --project "$PROJECT" | tail -n +2); do
    gcloud secrets versions destroy "$v" --secret "$SECRET_NAME" --project "$PROJECT" --quiet || true
  done
else
  echo "secret $SECRET_NAME already current"
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

# ---------------------------------------------------------------- pick the build source
# The real image is agent/Dockerfile built with the REPO ROOT as context (the agent package
# imports db/SCHEMA.md and shared modules). Until that exists we deploy a placeholder that
# proves the whole pipeline — build, registry, secret mount, public URL — end to end.
if [ -f "$REPO_ROOT/agent/Dockerfile" ]; then
  SRC="$REPO_ROOT"; DOCKERFILE="agent/Dockerfile"
  echo "--- building agent/Dockerfile (context = repo root)"
  [ -f "$REPO_ROOT/.gcloudignore" ] || cp gcloudignore.template "$REPO_ROOT/.gcloudignore"
else
  SRC="$PWD/placeholder"; DOCKERFILE="Dockerfile"
  echo "--- agent/Dockerfile not found; building deploy/cloudrun/placeholder (PIPELINE TEST)"
fi

# ---------------------------------------------------------------- build
# This project has no Compute Engine default service account, so Cloud Build must be told
# which identity to run as, and logs must go to a user-owned regional bucket.
gcloud builds submit "$SRC" \
  --project "$PROJECT" --region "$REGION" \
  --tag "${IMAGE}:${TAG}" \
  --service-account="projects/${PROJECT}/serviceAccounts/${RUNTIME_SA}" \
  --default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET --quiet
gcloud artifacts docker tags add "${IMAGE}:${TAG}" "${IMAGE}:latest" --quiet 2>/dev/null || true

# ---------------------------------------------------------------- deploy
gcloud run deploy "$SERVICE" \
  --project "$PROJECT" --region "$REGION" \
  --image "${IMAGE}:${TAG}" \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 1Gi --concurrency 40 --timeout 600 \
  --cpu-throttling \
  --execution-environment gen2 \
  --service-account "$RUNTIME_SA" \
  --labels app=slateiq,tier=agent \
  --set-secrets "GOOGLE_API_KEY=${SECRET_NAME}:latest" \
  --set-env-vars "^@^GOOGLE_GENAI_USE_VERTEXAI=FALSE@GOOGLE_CLOUD_PROJECT=${PROJECT}@GOOGLE_CLOUD_LOCATION=${REGION}@CLICKHOUSE_MCP_URL=${CLICKHOUSE_MCP_URL}@CLICKHOUSE_MCP_TOKEN=${CLICKHOUSE_MCP_TOKEN}@CLIPS_BASE_URL=${CLIPS_BASE_URL}@GRAFANA_URL=${GRAFANA_URL}" \
  --quiet

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" --format='value(status.url)')
echo
echo "SERVICE_URL=$URL"
echo -n "GET /health -> "; curl -fsS --max-time 30 "$URL/health" || echo "(no /health on this image)"
echo
