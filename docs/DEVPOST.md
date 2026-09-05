# Devpost text (draft — update with real numbers/URLs before submitting)

## Inspiration
Film crews generate enormous structured data every day (takes, slates, camera metadata, sound reports, script-supervisor notes) and then throw it into PDFs and spreadsheets. Editors re-watch everything; producers get a Daily Progress Report at 1 a.m. We asked: what if a production had a real analytical database and agents that both *fill* it from raw footage and *answer* from it?

## What it does
- **Ingest agents** (Gemini 3.5 Flash, multimodal): watch each dailies clip → transcript with speakers, action beats, quality flags (boom in shot, soft focus, line flub, audio clipping…), emotion intensity, circled-take recommendation; plus per-half-second telemetry (focus, exposure, motion, audio levels) from ffmpeg. Everything lands in ClickHouse.
- **Specialist agents** (Google ADK multi-agent: coordinator → editor / production / continuity / report): answer editor, 1st AD, script supervisor and producer questions by writing SQL and executing it **through the official ClickHouse MCP server at runtime** — the agent trace shows every query.
- **Documents**: generates the Daily Progress Report and Editor's Log (circled takes) and reads them aloud with Gemini TTS.
- **Production Health**: Grafana dashboards over the same ClickHouse tables.

## How we built it
Google ADK (python) + Gemini 3.x (google-genai) · mcp-clickhouse (StreamableHTTP) · ClickHouse 25.6 · Cloud Run (agent API + React UI, Grafana) · GCS (media) · Secret Manager · ffmpeg. Footage: *Tears of Steel* (Blender Foundation, CC-BY 3.0). Synthetic 30-day production data (~3k takes, >3M telemetry rows) so the analytics are realistic at scale.

## Challenges
mcp-clickhouse (MCP SDK 2.x) vs ADK (MCP SDK 1.x) dependency split → run the MCP server as its own service (which is also the right production shape). Keeping SQL generation trustworthy → schema doc injected into prompts, SELECT-only guardrail callbacks, golden-query evals. Fitting ClickHouse on a free-tier e2-micro.

## What's next
Live on-set ingest from camera cards, sound-report parsing, Avid/Resolve bin export, per-production Grafana alerts.
