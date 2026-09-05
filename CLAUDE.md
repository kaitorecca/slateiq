# SlateIQ — Dailies Intelligence for film production (Agentic Cinema Hackathon, ClickHouse track)

Read `docs/PLAN.md` first. Deadline: 9 Sep 2026 14:00 PDT. Judging: Tech implementation (Google Cloud + partner), Design (complete product), Impact, Idea quality — equal weight.

## Hard rules (do not violate)
- **Only Google AI** in the product: Gemini (google-genai / ADK), Gemini TTS, Imagen. NO OpenAI/Anthropic/other model APIs in product code. (Claude is only the dev tool.)
- **Partner = ClickHouse via the OFFICIAL MCP server (`mcp-clickhouse`)**, used at runtime by the agent. Never bypass it for agent reasoning (direct clickhouse-connect is allowed ONLY for ingest/seed/admin scripts).
- **Cost:** free tiers only. Cloud Run min-instances=0, 1x e2-micro VM (us-central1), GCS <5GB, no Agent Engine/GKE/Cloud SQL/BigQuery beyond free. Gemini calls: use `gemini-3.5-flash` / `gemini-3.1-flash-lite` for bulk; cache every Gemini result on disk (`data/cache/`) so re-runs are free. Never analyse >15 min of video total.
- No secrets in git. `.env` and `.secrets/` are gitignored. Repo will be PUBLIC (Apache-2.0).
- Each sprint: write/update design + tracking under `docs/`.

## Environments (two venvs on purpose — mcp-clickhouse needs mcp 2.x, ADK needs mcp 1.x)
- `.venv/` — ADK 2.8, google-genai, clickhouse-connect, fastapi. `source .venv/bin/activate`. Use `uv pip install`.
- `.venv-mcp/` — `mcp-clickhouse` 0.6 only. Start: `scripts/mcp_up.sh` → http://localhost:8765/mcp (health `/health`). Tools: `list_databases`, `list_tables`, `run_query` (read-only).
- Local ClickHouse: docker `slateiq-ch` → http://localhost:8123 user `default` / pass `clickhouse`. (Port 8000 is taken by Airbyte — never use it.)
- Env: `set -a; source .env; set +a` (GEMINI/GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT=gke-hackathon-472816, GOOGLE_APPLICATION_CREDENTIALS=.secrets/gcp-sa.json, CLICKHOUSE_*).
- ffmpeg: `~/miniconda3/envs/media/bin/ffmpeg`. Node 24 available. gcloud authed (project gke-hackathon-472816). `gh` authed (kaitorecca).
- ADK MCP import: `from google.adk.tools.mcp_tool.mcp_toolset import McpToolset`; `from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams` (set `timeout=30, sse_read_timeout=300`). Verified working smoke test: `docs/smoke_mcp_adk.py`.
- Gemini models verified with our key: gemini-3.5-flash, gemini-3.1-pro-preview, gemini-3.8-flash, gemini-3.1-flash-tts-preview, gemini-2.5-flash-preview-tts, imagen via gemini-3.1-flash-image, veo-3.1-*.

## Layout / ownership
| Dir | Owner | Contents |
|---|---|---|
| `db/` | data eng | DDL (`schema.sql`), synthetic production generator, seed scripts, MVs, `SCHEMA.md` (agent-facing schema doc) |
| `ingest/` | ingest eng | clip splitting (ffmpeg), Gemini multimodal analysis → JSON → ClickHouse |
| `agent/` | agent eng | ADK app package `slateiq_agent/` (root + sub-agents), FastAPI `main.py`, evals |
| `web/` | frontend | React+Vite UI (chat, takes gallery, reports, embedded Grafana) |
| `deploy/` | infra | VM bootstrap (docker compose: clickhouse + mcp-clickhouse + caddy), Cloud Run deploy scripts, Grafana provisioning |
| `docs/` | all | PLAN, ARCHITECTURE, TRACKING, DEMO_SCRIPT, SUBMISSION |
Don't edit another owner's dir without noting it in `docs/TRACKING.md`. Shared contracts live in `db/SCHEMA.md` and `docs/ARCHITECTURE.md`.
