#!/usr/bin/env bash
# Publish dailies clips + thumbnails to a public GCS bucket and print the base URL.
#
# Free tier: 5 GB-months standard storage in a US region, 5k class-A + 50k class-B ops,
# 100 GB/month egress to most destinations. Our whole clip set is well under 1 GB.
#
# Output: CLIPS_BASE_URL, which feeds `ingest/load.py --base-url` and the Cloud Run
# CLIPS_BASE_URL env var (the UI builds <base>/clips/<file>.mp4 playback links).
set -euo pipefail
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"

PROJECT="${PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
BUCKET="${BUCKET:-slateiq-media-${PROJECT}}"
DRY_RUN="${DRY_RUN:-0}"

echo "project=$PROJECT bucket=gs://$BUCKET region=$REGION"
gcloud services enable storage.googleapis.com --project "$PROJECT" --quiet >/dev/null

# ---------------------------------------------------------------- bucket
if gcloud storage buckets describe "gs://$BUCKET" --project "$PROJECT" >/dev/null 2>&1; then
  echo "bucket already exists"
else
  gcloud storage buckets create "gs://$BUCKET" \
    --project "$PROJECT" --location "$REGION" --default-storage-class STANDARD \
    --uniform-bucket-level-access --quiet
fi

# Public read for anonymous judges. Uniform access => a single IAM binding, no per-object ACLs.
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" \
  --member=allUsers --role=roles/storage.objectViewer --project "$PROJECT" --quiet >/dev/null
# CORS so the React UI (Cloud Run origin) can fetch/seek the media.
cat > /tmp/slateiq-cors.json <<'CORS'
[{"origin":["*"],"method":["GET","HEAD"],"responseHeader":["Content-Type","Range","Content-Range","Accept-Ranges"],"maxAgeSeconds":3600}]
CORS
gcloud storage buckets update "gs://$BUCKET" --cors-file=/tmp/slateiq-cors.json --project "$PROJECT" --quiet >/dev/null

# ---------------------------------------------------------------- upload
# Immutable, content-addressed-by-name media: cache hard so repeated demo playback is free.
upload() {  # $1=local dir  $2=remote prefix  $3.. = find predicates
  local dir="$1" prefix="$2"; shift 2
  [ -d "$dir" ] || { echo "  (no $dir, skip)"; return; }
  local files=()
  while IFS= read -r -d '' f; do files+=("$f"); done \
    < <(find "$dir" -maxdepth 1 -type f \( "$@" \) -print0)
  echo "--- $dir -> gs://$BUCKET/$prefix/  (${#files[@]} files)"
  [ "${#files[@]}" -eq 0 ] && return 0
  [ "$DRY_RUN" = 1 ] && return 0
  # The object prefix must match the relative clip_uri/thumb_uri stored in ClickHouse
  # ('clips/x.mp4', 'thumbs/x.jpg'), so the UI can build <base>/<uri> directly.
  gcloud storage cp --project "$PROJECT" \
    --cache-control="public, max-age=31536000, immutable" \
    --quiet "${files[@]}" "gs://$BUCKET/$prefix/"
}

upload "$REPO_ROOT/data/clips"  clips  -name '*.mp4' -o -name '*.mov' -o -name '*.webm'
upload "$REPO_ROOT/data/thumbs" thumbs -name '*.jpg' -o -name '*.jpeg' -o -name '*.png'
upload "$REPO_ROOT/data/clips"  clips  -name '*.jpg' -o -name '*.png' -o -name '*.vtt'

# ---------------------------------------------------------------- report
BASE="https://storage.googleapis.com/${BUCKET}"
echo
echo "objects:"; gcloud storage ls "gs://$BUCKET/**" --project "$PROJECT" 2>/dev/null | head -20
echo "total size:"; gcloud storage du -sh "gs://$BUCKET" --project "$PROJECT" 2>/dev/null || true
cat <<OUT

CLIPS_BASE_URL=$BASE
  ingest:    python ingest/load.py --base-url "$BASE/clips"
  cloud run: add CLIPS_BASE_URL=$BASE to .secrets/deploy.env, then deploy/cloudrun/deploy_agent.sh
OUT
