#!/usr/bin/env bash
# SlateIQ ingest — real footage -> Gemini -> ClickHouse. Idempotent end to end.
#
#   ./ingest/run_all.sh                 # cut, analyse (cached), load into ClickHouse
#   ./ingest/run_all.sh --force-clips   # re-encode every clip
#   ./ingest/run_all.sh --base-url https://storage.googleapis.com/slateiq-media
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

FORCE_CLIPS=""
LOAD_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force-clips) FORCE_CLIPS="--force"; shift ;;
    --base-url) LOAD_ARGS+=(--base-url "$2"); shift 2 ;;
    *) LOAD_ARGS+=("$1"); shift ;;
  esac
done

# shellcheck disable=SC1091
source .venv/bin/activate
if [[ -f .env ]]; then set -a; source .env; set +a; fi

cd "$REPO/ingest"

echo "== 1/5 cut clips =============================================="
python clips.py $FORCE_CLIPS

echo "== 2/5 gemini analysis (cached in data/cache) ================="
python analyze.py

echo "== 3/5 continuity notes ======================================="
python continuity.py

echo "== 4/5 load into ClickHouse ==================================="
python load.py --replace "${LOAD_ARGS[@]}"

echo "== 5/5 verify the whole dataset (db/verify.py) ================"
cd "$REPO"
python db/verify.py || echo "!! db/verify.py reported failures"

echo "== done ======================================================="
