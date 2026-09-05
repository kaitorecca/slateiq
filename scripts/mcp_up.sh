#!/usr/bin/env bash
# Start the official ClickHouse MCP server (HTTP transport).
#
# Everything is overridable from the environment or .env, so a second stack can
# run beside the first:
#   CLICKHOUSE_MCP_BIND_PORT=28765 scripts/mcp_up.sh
#
# Defaults: 0.0.0.0:8765, auth disabled (local dev only).
cd "$(dirname "$0")/.."
set -a; [[ -f .env ]] && source .env; set +a

: "${CLICKHOUSE_MCP_BIND_HOST:=0.0.0.0}"
: "${CLICKHOUSE_MCP_BIND_PORT:=8765}"
: "${CLICKHOUSE_MCP_ALLOWED_HOSTS:=127.0.0.1:${CLICKHOUSE_MCP_BIND_PORT},localhost:${CLICKHOUSE_MCP_BIND_PORT}}"
: "${CLICKHOUSE_MCP_SERVER_TRANSPORT:=http}"
: "${CLICKHOUSE_MCP_AUTH_DISABLED:=true}"

export CLICKHOUSE_MCP_SERVER_TRANSPORT CLICKHOUSE_MCP_AUTH_DISABLED \
       CLICKHOUSE_MCP_BIND_HOST CLICKHOUSE_MCP_BIND_PORT CLICKHOUSE_MCP_ALLOWED_HOSTS

echo "mcp-clickhouse -> http://${CLICKHOUSE_MCP_BIND_HOST}:${CLICKHOUSE_MCP_BIND_PORT}/mcp" \
     "(clickhouse ${CLICKHOUSE_HOST:-localhost}:${CLICKHOUSE_PORT:-8123})" >&2
exec .venv-mcp/bin/python -m mcp_clickhouse.main
