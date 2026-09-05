# `scripts/` — local helpers

Two small scripts. Neither is on the product's runtime path; they exist so the local
environment matches the deployed one.

| File | What it does |
|---|---|
| `mcp_up.sh` | Starts the **official** `mcp-clickhouse` server (HTTP transport) on **:8765** from the separate `.venv-mcp/` environment, reading credentials from `.env`. This is the only data path the agents use — health at <http://localhost:8765/health>, MCP at `/mcp`. |
| `smoke_mcp_adk.py` | ~15-line proof that ADK's `McpToolset` can reach that server: one `LlmAgent`, `StreamableHTTPConnectionParams`, ask it to list databases and `SELECT version()`. Prints every tool call. Run it when the MCP wiring looks wrong before debugging the real agent. |

```bash
scripts/mcp_up.sh &                                  # :8765
.venv/bin/python scripts/smoke_mcp_adk.py            # needs GOOGLE_API_KEY
```

Two virtualenvs on purpose: ADK 2.8 pins `mcp` 1.x while `mcp-clickhouse` needs `mcp` 2.x,
so the MCP server lives in `.venv-mcp/` and is reached over HTTP.
