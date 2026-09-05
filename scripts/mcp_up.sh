#!/usr/bin/env bash
# Start official ClickHouse MCP server (HTTP transport) on :8765
cd "$(dirname "$0")/.."; set -a; source .env; set +a
export CLICKHOUSE_MCP_SERVER_TRANSPORT=http CLICKHOUSE_MCP_AUTH_DISABLED=true CLICKHOUSE_MCP_BIND_HOST=0.0.0.0 CLICKHOUSE_MCP_BIND_PORT=8765
export CLICKHOUSE_MCP_ALLOWED_HOSTS="127.0.0.1:8765,localhost:8765"
exec .venv-mcp/bin/python -m mcp_clickhouse.main
