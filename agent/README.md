# SlateIQ — agent service

A multi-agent network built on **Google Cloud Agent Builder (Agent Development
Kit / ADK)** that answers film-production questions by generating SQL and
executing it **through the official ClickHouse MCP server** (`mcp-clickhouse`,
StreamableHTTP), wrapped in a FastAPI app that also serves the React UI, the
generated reports and Gemini TTS audio.

Industry terms used throughout: the **director circles** a take and the
**script supervisor** records it; **print ratio** = takes per circled take (not
"shooting ratio", which compares footage shot to footage in the final cut);
pages are eighths, so 8/8 is "1 page" and anything else reads like "2 3/8
pages"; the generated document is the **Daily Progress Report** (script
supervisor / AD department), not the 2nd AD's Daily Production Report.

```
        ┌────────────────── slateiq_coordinator (LlmAgent) ──────────────────┐
        │  routes by transfer_to_agent, keeps the conversation human         │
        └───┬──────────────┬──────────────────┬────────────────────┬─────────┘
            │              │                  │                    │
      editor_agent   production_agent   continuity_agent      report_agent
      takes, lines,  schedule, pages,   cross-take conflicts, DPR + Editor's
      flags, clips   print ratio      line variations       Log markdown
            └──────────────┴──────────────────┴────────────────────┘
                                    │
                       one shared McpToolset (StreamableHTTP)
                                    │
                   mcp-clickhouse  →  ClickHouse `slateiq`
```

Every specialist has exactly one data tool: the ClickHouse MCP toolset. There
is no direct database driver on the reasoning path — the only
`clickhouse-connect` call in this service is the `/api/takes` gallery listing,
which does no reasoning and is labelled as such in `main.py`.

## Layout

| Path | What |
|---|---|
| `slateiq_agent/agent.py` | agents + the shared `McpToolset`; exports `root_agent` |
| `slateiq_agent/prompts.py` | instructions (domain playbooks, SQL rules, JSON contract) |
| `slateiq_agent/schema.py` | loads `db/SCHEMA.md` at runtime, embedded fallback |
| `slateiq_agent/guardrails.py` | `before_tool_callback` SELECT-only, `after_tool_callback` truncation |
| `slateiq_agent/runtime.py` | Runner + event normalisation shared by API and evals |
| `slateiq_agent/config.py` | all env-var configuration |
| `main.py` | FastAPI app (ADK app + SlateIQ routes + static) |
| `evals/questions.yaml` | 16 questions across editor / script supervisor / AD / producer / director |
| `evals/run_eval.py` | runs them for real, Gemini-judges them, writes `last_run.md` |

## Run locally

```bash
cd /path/to/block
source .venv/bin/activate
set -a && source .env && set +a
scripts/mcp_up.sh &                 # mcp-clickhouse on :8765 (health: /health)

cd agent
uvicorn main:app --port 8811        # 8811 is the SlateIQ default on this box
```

Then:
- `http://localhost:8811/` — the React UI if `web/dist` exists
- `http://localhost:8811/dev-ui/` — the ADK developer UI (agent tree, traces)
- `http://localhost:8811/docs` — OpenAPI

Ports 8080 (WeKnora) and 3000 (Chatwoot) are taken on the dev box; Cloud Run
injects `$PORT`, which the Dockerfile honours.

## Environment

| Var | Default | Purpose |
|---|---|---|
| `CLICKHOUSE_MCP_URL` | `http://localhost:8765/mcp` | MCP endpoint — point at the hosted server on deploy |
| `CLICKHOUSE_MCP_TOKEN` | *(unset)* | sent as `Authorization: Bearer …` |
| `CLICKHOUSE_MCP_TIMEOUT` / `_SSE_READ_TIMEOUT` | `30` / `300` | seconds |
| `SLATEIQ_MODEL` | `gemini-3.5-flash` | coordinator + specialists |
| `SLATEIQ_REPORT_MODEL` | = `SLATEIQ_MODEL` | set to `gemini-3.1-pro-preview` for richer DPRs |
| `SLATEIQ_TTS_MODEL` / `SLATEIQ_TTS_VOICE` | `gemini-2.5-flash-preview-tts` / `Kore` | `/api/tts` |
| `SLATEIQ_JUDGE_MODEL` | `gemini-3.5-flash` | eval judge |
| `SLATEIQ_DB` | `slateiq` | database name used in the prompts |
| `SLATEIQ_MAX_ROWS` | `200` | hard LIMIT ceiling enforced by the guardrail |
| `SLATEIQ_MAX_TOOL_RESULT_CHARS` | `24000` | tool-result truncation |
| `SLATEIQ_SCHEMA_MD` | `<repo>/db/SCHEMA.md` | schema contract injected into instructions |
| `SLATEIQ_WEB_DIST` | `<repo>/web/dist` | static UI, skipped if absent |
| `CLIPS_DIR` | `<repo>/data/clips` | mounted at `/clips` |
| `SLATEIQ_SESSION_DB_URI` | `sqlite:///agent/sessions.db` | ADK session store |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | — | Gemini auth |
| `CLICKHOUSE_HOST/PORT/USER/PASSWORD/SECURE` | — | **only** for `/api/takes` |

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | model + MCP config, whether `web/dist` and clips exist |
| POST | `/api/chat` | **SSE**. Body `{message, session_id?, user_id?, agent?}` |
| GET | `/api/report/dpr?day=12` | Daily Progress Report → `{day, markdown, sql[], ran_query}` |
| GET | `/api/report/editor-log?day=12` | Editor's Log, same shape |
| POST | `/api/tts` | `{text, voice?, summarize?}` → `audio/wav` bytes of a ≤90-word read |
| GET | `/api/takes?scene=&day=&status=&limit=` | direct-ClickHouse gallery listing |
| GET | `/clips/*` | local clip files |
| — | `/dev-ui`, `/run`, `/run_sse`, `/apps/*` | provided by ADK's `get_fast_api_app` |

### `/api/chat` SSE event stream

Each frame is `event: <type>` + `data: <json>`:

| `type` | payload |
|---|---|
| `session` | `{session_id, agent}` — pass `session_id` back to continue the conversation |
| `agent` | `{name}` — which specialist has the floor (drives the "editor_agent is looking…" chip) |
| `text` | `{delta}` — token deltas as the answer is written |
| `tool_call` | `{id, name, args}` — `name:"run_query"` carries the generated SQL in `args.query` |
| `tool_result` | `{id, name, rows, summary}` — truncated preview of what came back |
| `final` | `{text, sql[], takes[], session_id}` |
| `error` | `{message}` |
| `done` | end of stream |

```bash
curl -N -X POST localhost:8811/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Which takes have boom in shot on day 12?"}'
```

### Structured take output (UI contract)

When an answer references takes, the agents append a fenced JSON block as the
last thing in the message:

````markdown
```json
{"takes":[{"take_id":"TOS-D12-S6-A-06-B",
           "clip_uri":"gs://slateiq-dailies/tos2026/d12/…mp4",
           "t":13.6,
           "label":"6/A/6 circled",
           "reason":"boom dips in at 13.6s"}],
 "sql":["SELECT … LIMIT 100"]}
```
````

- `take_id`, `clip_uri` come straight from `slateiq.take`; `t` is the seek
  offset in seconds (from `take_event.t_offset_s`, or 0 for the whole take).
- At most 12 takes. The block is omitted when no takes are involved.
- The prose above the block always stands on its own.
- `runtime.parse_structured_block()` parses it; the `final` SSE event exposes
  it pre-parsed as `takes` and `sql`, so the UI does not have to.

## Guardrails

`before_tool_callback` (`guardrails.enforce`) runs on every `run_query`:

- must be a **single** statement starting with `SELECT` or `WITH`
- destructive statements (`INSERT INTO`, `DROP`, `ALTER TABLE`, `SYSTEM FLUSH`,
  `GRANT`, …) and `INTO OUTFILE` are rejected with an explanatory tool result
  the model can recover from
- a missing `LIMIT` is **appended** and an oversized one **clamped** to
  `SLATEIQ_MAX_ROWS` (200) rather than bounced, so the model does not waste a
  round-trip; the rewritten SQL is what actually executes
- the executed SQL is recorded on session state (`slateiq_sql`) for the trace

`after_tool_callback` truncates any tool result over
`SLATEIQ_MAX_TOOL_RESULT_CHARS` and tells the model to re-query with tighter
filters — `frame_telemetry` alone is 3M+ rows.

## Evals

```bash
cd /path/to/block && source .venv/bin/activate && set -a && source .env && set +a
python agent/evals/run_eval.py                     # all 16, judged
python agent/evals/run_eval.py --only dpr forecast # subset
python agent/evals/run_eval.py --no-judge          # no Gemini judging
```

Each question is run through the real coordinator against the real MCP server.
The harness records routing, every tool call, the SQL, latency and whether
`run_query` was actually reached, then a Gemini judge scores 1–5 against the
per-question rubric. Results land in `evals/last_run.md` (human) and
`evals/last_run.json` (machine). The run exits non-zero if any question with
`must_query: true` answered without touching MCP.

See [`evals/last_run.md`](evals/last_run.md) for the latest numbers.

## Docker

The build context is the **repo root** (the image needs `db/SCHEMA.md` and
`web/dist`):

```bash
docker build -f agent/Dockerfile -t slateiq-agent .
docker run -p 8811:8080 --env-file .env \
  -e CLICKHOUSE_MCP_URL=https://mcp.example.com/mcp \
  -e CLICKHOUSE_MCP_TOKEN=… slateiq-agent
```

## Notes

- ADK 2.8 pins `mcp` 1.x while `mcp-clickhouse` needs `mcp` 2.x — that is why
  the MCP server lives in its own venv (`.venv-mcp`) / container and is reached
  over HTTP rather than stdio.
- One `McpToolset` instance is shared by all five agents. ADK does not reparent
  toolsets the way it reparents sub-agents, so a single instance keeps a single
  MCP connection for the whole network.
- `db/SCHEMA.md` is re-read whenever its mtime changes; if it is missing the
  agents fall back to the embedded summary in `slateiq_agent/schema.py`.
