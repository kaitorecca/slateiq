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
is no direct database driver on the reasoning path. The only
`clickhouse-connect` calls in this service are the `/api/takes` gallery
listing, `/api/take/{id}/events` and the Editor's Log export
(`/api/export/editors-log`) — UI and file-export paths that run one fixed,
parameterised SELECT, involve no LLM and generate no SQL. All three are
labelled as such in `main.py` and `slateiq_agent/export.py`.

## Layout

| Path | What |
|---|---|
| `slateiq_agent/agent.py` | agents + the shared `McpToolset`; exports `root_agent` |
| `slateiq_agent/prompts.py` | instructions (domain playbooks, SQL rules, JSON contract) |
| `slateiq_agent/schema.py` | loads `db/SCHEMA.md` at runtime, embedded fallback |
| `slateiq_agent/guardrails.py` | `before_tool_callback` SELECT-only, `after_tool_callback` truncation |
| `slateiq_agent/runtime.py` | Runner + event normalisation shared by API and evals |
| `slateiq_agent/config.py` | all env-var configuration |
| `slateiq_agent/export.py` | Editor's Log export — CSV / ALE / Markdown (non-reasoning path) |
| `main.py` | FastAPI app (ADK app + SlateIQ routes + static) |
| `tests/` | pytest unit tests for the guardrail and the export |
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
| `CLICKHOUSE_HOST/PORT/USER/PASSWORD/SECURE` | — | **only** for `/api/takes`, `/api/take/{id}/events` and `/api/export/editors-log` |

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | model + MCP config, whether `web/dist` and clips exist |
| POST | `/api/chat` | **SSE**. Body `{message, session_id?, user_id?, agent?}` |
| GET | `/api/report/dpr?day=12` | Daily Progress Report → `{day, markdown, sql[], ran_query}` |
| GET | `/api/report/editor-log?day=12` | Editor's Log, same shape |
| GET | `/api/export/editors-log?day=12&format=csv\|ale\|md` | circled takes as a downloadable file — CSV, **ALE** (Avid Log Exchange) or Markdown |
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

## Editor's Log export (CSV / ALE / Markdown)

```
GET /api/export/editors-log?day=12&format=csv|ale|md[&status=circled,hold]
```

The circled-take list an assistant editor carries from the set into the cutting
room, as a file. **Export Editor's Log (CSV)** / **ALE** sit next to the DPR
button on Production Health.

Every format carries the same rows — one per circled camera slate, ordered by
scene (numerically, so `102` does not sort ahead of `12`), shot, take, camera:
scene + slug, shot, take, camera, camroll, soundroll, TC in / out, duration,
status, the director's note, Gemini's summary, the quality score and the QC
flags.

**ALE** is Avid Log Exchange, what Media Composer has imported since the 1990s:
tab-delimited, CRLF, three sections —

```
Heading
FIELD_DELIM	TABS
VIDEO_FORMAT	1080
AUDIO_FORMAT	48khz
FPS	25

Column
Name	Tracks	Start	End	Duration	Scene	Take	Camroll	Soundroll	Comments	…

Data
12/B/2-B	V A1A2	12:26:18:20	12:26:35:01	00:00:16:05	12	2	B012	S012	Cleaner. Print.	…
```

The ten standard columns map straight onto Avid bin columns; the SlateIQ extras
(`Shot`, `Camera`, `Circled`, `Labroll`, `Quality`, `Flags`, `Summary`) arrive
as custom ones. `End` is exclusive, timecode is non-drop at the take's own
`fps`, and every value is collapsed to a single line so a stray tab or newline
in a director's note cannot shift a column.

This is an **export path, not an agent path**: `slateiq_agent/export.py` runs
one fixed, parameterised SELECT through `clickhouse-connect`. No model is
involved and no SQL is generated. Analytical answers still go through
`mcp-clickhouse`.

```bash
curl -s 'localhost:8811/api/export/editors-log?day=12&format=ale' -o day12.ale
```

## Surviving an MCP restart

`SelfHealingMcpToolset` (`slateiq_agent/agent.py`) is the shared toolset. ADK
pools one streamable-HTTP session per toolset and retries *session creation*,
but never the tool listing or the tool call — so the first question asked after
`mcp-clickhouse` restarted came back as a developer error
(`ValueError: Tool 'run_query' not found`) and only the second one worked.

The subclass notices a transport-shaped failure — on `get_tools` or on any tool
call — drops the pooled session and runs the call once more against a fresh
one. A ClickHouse error (bad SQL, unknown column) is *not* transport-shaped and
is never retried: the model has to see it and fix its own query. Every MCP tool
here is a read-only SELECT, so replaying one cannot duplicate a side effect.

Verified: kill `mcp_clickhouse.main`, restart with `scripts/mcp_up.sh`, ask a
question — answered on the first try in 3.8 s, with
`MCP session reset — reconnecting` in the log where the failure used to be.

## Tests

```bash
cd /path/to/block && source .venv/bin/activate
uv pip install pytest
python -m pytest agent/tests -q          # 113 passed in ~1.5s
```

No database, no MCP server, no model, no network — pure text in / text out, so
they are safe to run anywhere.

| File | Covers |
|---|---|
| `tests/test_guardrails.py` | SELECT-only + the DDL/DML keyword list; multi-statement; `system.*` reads (QC #2 **G-1**); external table functions `url()/file()/remote()/s3()/…` (**G-2**); unbounded `groupArray` over `frame_telemetry` (**G-3**); LIMIT appended / clamped / kept ahead of `FORMAT` and `SETTINGS` (**G-4**); comment stripping and keyword matching inside string literals (**G-5**); injection payloads; MCP-down message translation; tool-result truncation |
| `tests/test_selfheal.py` | which failures the self-healing toolset retries (dead session, refused connection, read timeout, 5xx) and which it must hand back untouched (a ClickHouse `Code: 47`, a guardrail rejection), one retry only, no double-wrapping |
| `tests/test_export.py` | timecode round-trips and frame clamping; `End = Start + Duration`; ALE section order, column order and one field per column; tabs / newlines in a note; empty day; FPS taken from the footage; CSV quoting and columns; Markdown grouping; format dispatch; and that the export SQL is a single parameterised SELECT that also passes the agent guardrail |

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

### Latest run (16 questions, real MCP + real ClickHouse, 2026-09-05)

| Metric | Result |
|---|---|
| Reached MCP `run_query` | **16 / 16 (100%)** |
| Gemini judge score | **mean 4.88 / 5**, median 5, min 4, **16/16 at 4+** |
| Routed to the expected specialist | 15 / 16 (`ng_rate` went to `production_agent` instead of `editor_agent` — defensible) |
| Latency | mean 63.1s, median 39.3s, max 257.1s (`line_variations`) |
| Wall clock | 411s for all 16 at concurrency 3 |

The two report questions (`dpr`, `editors_log`) are the expensive ones — 17 and
11 queries — because they build a full document. Everything else averages 3–4
queries. Full trace, SQL and answers: [`evals/last_run.md`](evals/last_run.md)
(machine-readable in `evals/last_run.json`).

The judge sees the truncated tool results as well as the SQL, so "grounded"
means *the numbers appear in what ClickHouse returned*, not merely that a query
was run.

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
