#!/usr/bin/env bash
# SlateIQ data-plane healthcheck — run from the laptop, no SSH required for the core checks.
#
#   deploy/vm/healthcheck.sh          # the seven checks below
#   deploy/vm/healthcheck.sh --ssh    # also ask the VM about containers, RAM and the systemd unit
#   deploy/vm/healthcheck.sh --quiet  # exit code only (for cron / a watch loop)
#
# Exit 0 = everything green, 1 = at least one check failed. Every check prints the value it
# saw, so a red line is actionable without re-running anything by hand.
set -uo pipefail
cd "$(dirname "$0")/../.."          # repo root

QUIET=0; WITH_SSH=0
for a in "$@"; do
  case "$a" in
    --quiet|-q) QUIET=1 ;;
    --ssh) WITH_SSH=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

[ -f .secrets/deploy.env ] || { echo "missing .secrets/deploy.env — run deploy/vm/deploy_stack.sh"; exit 1; }
set -a; . ./.secrets/deploy.env; set +a
: "${PUBLIC_HOST:?}" "${CLICKHOUSE_MCP_TOKEN:?}" "${CH_AGENT_RO_PASSWORD:?}"

VM="${VM:-slateiq-data}"; ZONE="${ZONE:-us-central1-a}"
LOCAL_CH="${LOCAL_CH:-http://localhost:8123}"
LOCAL_CH_USER="${LOCAL_CH_USER:-default}"; LOCAL_CH_PASS="${LOCAL_CH_PASS:-clickhouse}"
FAIL=0

say()  { [ "$QUIET" = 1 ] || printf '%s\n' "$*"; }
ok()   { say "  ok    $1"; }
bad()  { say "  FAIL  $1"; FAIL=1; }
head_() { say ""; say "$1"; }

# ---------------------------------------------------------------- 1. MCP liveness (no auth)
head_ "1. MCP /health"
H_BODY=$(curl -fsS --max-time 15 "https://$PUBLIC_HOST/health" 2>/dev/null)
[ "$H_BODY" = "OK" ] && ok "https://$PUBLIC_HOST/health -> OK" || bad "https://$PUBLIC_HOST/health -> '${H_BODY:-<no response>}' (expected OK)"

# ---------------------------------------------------------------- 2. MCP requires the bearer token
head_ "2. MCP auth"
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 -X POST "https://$PUBLIC_HOST/mcp" 2>/dev/null)
[ "$CODE" = "401" ] && ok "unauthenticated POST /mcp -> 401" || bad "unauthenticated POST /mcp -> $CODE (expected 401 — the endpoint may be open)"

# ---------------------------------------------------------------- 3. MCP initialize with the token
head_ "3. MCP handshake"
INIT=$(curl -fsS --max-time 20 "https://$PUBLIC_HOST/mcp" \
  -H "Authorization: Bearer $CLICKHOUSE_MCP_TOKEN" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1"}}}' 2>/dev/null)
case "$INIT" in
  *mcp-clickhouse*) ok "initialize -> $(printf '%s' "$INIT" | grep -o '"name":"mcp-clickhouse","version":"[^"]*"' | head -1)" ;;
  *) bad "initialize -> ${INIT:-<no response>}" ;;
esac

# ---------------------------------------------------------------- 4. ClickHouse ping through Caddy
head_ "4. ClickHouse /ch/ping"
P=$(curl -fsS --max-time 15 "https://$PUBLIC_HOST/ch/ping" 2>/dev/null | tr -d '[:space:]')
[ "$P" = "Ok." ] && ok "https://$PUBLIC_HOST/ch/ping -> Ok." || bad "https://$PUBLIC_HOST/ch/ping -> '${P:-<no response>}'"

# ---------------------------------------------------------------- 5. row counts hosted vs local
head_ "5. Row counts (hosted vs local)"
TABLES="${TABLES:-take take_event take_analysis scene shooting_day continuity_note frame_telemetry}"
for t in $TABLES; do
  R=$(curl -fsS --max-time 30 -X POST "https://$PUBLIC_HOST/ch?query=SELECT+count()+FROM+slateiq.$t" \
        --user "agent_ro:$CH_AGENT_RO_PASSWORD" 2>/dev/null | tr -d '[:space:]')
  L=$(curl -fsS --max-time 30 "$LOCAL_CH/?query=SELECT+count()+FROM+slateiq.$t" \
        --user "$LOCAL_CH_USER:$LOCAL_CH_PASS" 2>/dev/null | tr -d '[:space:]')
  if [ -z "$R" ]; then bad "slateiq.$t hosted=<query failed>"
  elif [ -z "$L" ]; then say "  skip  slateiq.$t hosted=$R (local ClickHouse not reachable at $LOCAL_CH)"
  elif [ "$R" = "$L" ]; then ok "slateiq.$t hosted=$R == local=$L"
  else bad "slateiq.$t hosted=$R != local=$L"
  fi
done

# ---------------------------------------------------------------- 6. least privilege still holds
head_ "6. agent_ro least privilege"
QL=$(curl -sS --max-time 20 -X POST "https://$PUBLIC_HOST/ch?query=SELECT+count()+FROM+system.query_log" \
      --user "agent_ro:$CH_AGENT_RO_PASSWORD" 2>/dev/null)
case "$QL" in
  *ACCESS_DENIED*) ok "SELECT FROM system.query_log -> ACCESS_DENIED (code 497)" ;;
  *) bad "SELECT FROM system.query_log -> '${QL:0:120}' (expected ACCESS_DENIED)" ;;
esac
WR=$(curl -sS --max-time 20 -X POST "https://$PUBLIC_HOST/ch?query=CREATE+TABLE+slateiq.hc_probe(x+Int8)+ENGINE=Memory" \
      --user "agent_ro:$CH_AGENT_RO_PASSWORD" 2>/dev/null)
case "$WR" in
  *ACCESS_DENIED*|*READONLY*) ok "CREATE TABLE -> refused ($(printf '%s' "$WR" | grep -o 'Code: [0-9]*' | head -1))" ;;
  *) bad "CREATE TABLE -> '${WR:0:120}' (expected refusal — agent_ro can WRITE)" ;;
esac

# ---------------------------------------------------------------- 7. Cloud Run agent
head_ "7. Cloud Run agent"
APP="${APP_URL:-https://slateiq-957930801789.us-central1.run.app}"
A=$(curl -fsS --max-time 60 "$APP/api/health" 2>/dev/null)
case "$A" in
  *'"mcp":"up"'*'"clickhouse":"up"'*) ok "$APP/api/health -> mcp up, clickhouse up" ;;
  "") say "  skip  $APP/api/health unreachable (cold start >60 s, or the service is being redeployed)" ;;
  *) bad "$APP/api/health -> ${A:0:160}" ;;
esac

# ---------------------------------------------------------------- 8. optional: the VM itself
if [ "$WITH_SSH" = 1 ]; then
  head_ "8. VM (ssh)"
  OUT=$(gcloud compute ssh "$VM" --zone "$ZONE" --command \
    'docker compose -f /opt/slateiq/docker-compose.yml ps --format "{{.Name}} {{.Status}}"; echo "--"; systemctl is-enabled slateiq-stack.service; systemctl is-active slateiq-stack.service; echo "--"; free -m | head -2' \
    < /dev/null 2>/dev/null)
  if [ -z "$OUT" ]; then bad "ssh to $VM failed"; else
    printf '%s\n' "$OUT" | sed 's/^/  /'
    printf '%s' "$OUT" | grep -q 'slateiq-ch .*healthy'  && ok "clickhouse healthy"          || bad "clickhouse not healthy"
    printf '%s' "$OUT" | grep -q 'slateiq-mcp .*healthy' && ok "mcp healthy"                 || bad "mcp not healthy"
    printf '%s' "$OUT" | grep -qx 'enabled'              && ok "slateiq-stack.service enabled (survives reboot)" || bad "slateiq-stack.service not enabled"
  fi
fi

say ""
if [ "$FAIL" = 0 ]; then say "ALL CHECKS PASSED"; else say "SOME CHECKS FAILED"; fi
exit "$FAIL"
