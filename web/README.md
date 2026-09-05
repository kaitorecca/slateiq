# SlateIQ — Web UI

React 18 + Vite + TypeScript + Tailwind front end for **SlateIQ**, the dailies-intelligence
production brain. Dark "cutting-room" aesthetic, film-slate motif.

It is a single-page app with four screens, served as static files by the FastAPI app in `agent/`.

| Screen | Route | What it does |
|---|---|---|
| **Ask the Dailies** | `#/ask` (default) | Streaming chat with the ADK agent + a live **Agent trace** panel showing which sub-agent is active and every `mcp-clickhouse` tool call with syntax-highlighted, copyable SQL and row counts. Take cards render an inline `<video>` that seeks to the cited timestamp. |
| **Takes** | `#/takes` | Scene + status filters over a grid of take cards (thumb, status badge, flag chips, quality bar, Gemini summary). Clicking a card opens a player drawer with the transcript / flag timeline. |
| **Production Health** | `#/health` | Embedded Grafana panels (or in-app recharts fallback), plus **Generate Daily Progress Report** → rendered markdown → **Read it aloud** via Gemini TTS, and **Export Editor's Log (CSV / ALE)** — the day's circled takes as a spreadsheet or an Avid Log Exchange file. |
| **About** | `#/about` | Inline-SVG architecture diagram, repo link, **Live** endpoint table (Cloud Run / Grafana / MCP health), screenshot strip, a "How it complies" block, and Tears of Steel CC-BY attribution. |

The header shows live connection health dots for MCP and ClickHouse, polled from `/api/health`.

Hosted URLs and media/footage policy live in one place: **`src/config.ts`** (all values overridable at
build time — see *Environment variables* below). Screenshots for the About strip are in `public/img/`.

## Run it

Node 24. From `web/`:

```bash
npm install

# Terminal A — the real backend (agent/) on :8811, OR the bundled mock:
npm run mock            # zero-dependency mock API on :8811

# Terminal B
npm run dev             # Vite on http://localhost:5188
```

`npm run dev:all` starts both in one terminal.

The dev server proxies `/api` and `/clips` to `http://localhost:8811`. Override with
`VITE_API_TARGET=http://host:port npm run dev`. Override the dev port with `PORT=5190 npm run dev`.

### Mock backend

`mock/server.mjs` implements the whole API contract with no dependencies — SSE chat with fake
agent/tool events, 24 synthetic takes, take events, a DPR, and a WAV beep for TTS. Use it to work on
the UI without ClickHouse, MCP or Gemini running. Clips 404 in mock mode; the UI degrades to a
striped placeholder, which is expected.

## Build

```bash
npm run build           # tsc -b && vite build  ->  web/dist
npm run preview
```

`web/dist` is committed so the Docker image can copy it without a Node build step.
Vite `base` is `/`, so FastAPI can mount `dist` at the site root.

## Environment variables

Build-time only (Vite inlines them), all optional:

| Var | Default | Effect |
|---|---|---|
| `VITE_GRAFANA_URL` | *(unset)* | When set, Production Health embeds Grafana `d-solo` panels instead of the in-app charts. |
| `VITE_GRAFANA_DASHBOARD` | `slateiq/production-health` | Dashboard uid/slug used in the `d-solo` URL. |
| `VITE_GRAFANA_PANELS` | `1:Print ratio by scene,2:Pages vs plan,3:Flag rate,4:Camera hours` | Comma-separated `panelId:Title` list. |
| `VITE_APP_URL` | `https://slateiq-hbissixc2q-uc.a.run.app` | Hosted app URL shown in the About page's **Live** section. |
| `VITE_MCP_HEALTH_URL` | `https://35.239.36.85.sslip.io/health` | Unauthenticated `mcp-clickhouse` health route, linked from **Live**. |
| `VITE_PUBLIC_MEDIA_BUCKETS` | `slateiq-media-gke-hackathon-472816` | Comma-separated GCS buckets that are public-read. A `gs://` `clip_uri` in any *other* bucket is treated as unpublished and renders a **"Media not published"** card instead of a dead `<video>`. |
| `VITE_FOOTAGE_SCENES` | `12,14A,27,33,41,56,78,102` | Scenes with real ingested footage. The Takes gallery opens on these ("Scenes with footage"); *All scenes* shows the whole synthetic shoot. |
| `VITE_API_TARGET` | `http://localhost:8811` | Dev-server proxy target only; irrelevant in production. |

## API contract this UI expects

All paths are same-origin.

- `POST /api/chat` — body `{session_id?, message}`. Responds `text/event-stream`. Each record is a
  JSON object (the client accepts `data: {...}` SSE framing **and** bare NDJSON lines):
  - `{"type":"agent","name":"editor_agent"}` — which sub-agent took over
  - `{"type":"tool_call","name":"run_query","args":{"query":"SELECT …"}}`
  - `{"type":"tool_result","name":"run_query","summary":"…","rows":812}`
  - `{"type":"text","delta":"…"}` — incremental answer text
  - `{"type":"final","text":"…","session_id":"…"}` — full answer; replaces the streamed text
  - `{"type":"error","message":"…"}` — optional
- `GET /api/takes?scene=12&day=&status=&limit=` → `{count, source, takes:[{take_id, scene_number,
  shot, take_number, status, clip_uri, thumb_uri, duration_s, quality_score, flags[], summary}]}`.
  A bare array is also accepted (the mock returns one). `scene` omitted ⇒ all takes.
  `scene_number` is a **string** — `14A` is a real scene number.
- `GET /api/take/<id>/events` → `{take, events:[{t_offset_s, kind, speaker, text, flag_type,
  severity}], …}`, or a bare array of `{t, kind, speaker, text, flag}`. Both are normalised
  client-side. **Optional** — a 404 just hides the transcript timeline.
- `GET /api/report/dpr?day=12` → `{markdown, day}`.
- `GET /api/export/editors-log?day=12&format=csv|ale|md` → the file itself, with a
  `Content-Disposition: attachment` filename. The Production Health buttons are plain
  `<a download>` links, so this is a normal browser download — no fetch, no blob.
- `POST /api/tts` `{text}` → `audio/mpeg` or `audio/wav` bytes.
- `GET /api/health` → `{ok, mcp:"up"|"down", clickhouse:"up"|"down"}`.
- `GET /clips/<file>.mp4`, `GET /thumbs/<file>.jpg`.

Notes for the backend:

- `clip_uri` / `thumb_uri` may be relative (`clips/x.mp4`), absolute `https://…`, or `gs://bucket/…`.
  A `gs://` URI is rewritten to `https://storage.googleapis.com/…` **only** for buckets listed in
  `VITE_PUBLIC_MEDIA_BUCKETS`; anything else renders a "Media not published" placeholder.
- When `thumb_uri` is missing the poster is derived from `clip_uri` by swapping `clips/` → `thumbs/`
  and the extension for `.jpg` (the layout both on disk and in the bucket).
- `status` is matched case-insensitively against `circled` / `ng` / `hold`; anything else renders as
  a neutral badge.
- `quality_score` may be 0–1 or 0–100.
- The **final answer text may end with a fenced ```json block** of the form
  `{"takes":[{take_id, clip_uri, t?, label?, reason?}], "sql":[…]}`.
  The UI parses it out of the visible markdown and renders players + a SQL disclosure. Any other
  fenced JSON is left in the prose untouched. The agents only reliably emit `take_id` / `clip_uri`,
  so `/api/chat` **enriches** each cited take with `scene_number / shot / take_number / status /
  thumb_uri / quality_score / summary` from ClickHouse before the `final` event is sent; the UI
  additionally falls back to parsing the slate out of `take_id`.
- `tool_result.rows` must be the real row count of the query result (mcp-clickhouse wraps it in a
  FastMCP `content[].text` JSON envelope), and `-1` for non-query tools such as ADK's
  `transfer_to_agent` — the trace panel hides the row chip and labels those "ADK routing" rather
  than overstating the partner evidence.
- Send `agent` / `tool_call` / `tool_result` events as they happen — the trace panel is the visible
  proof that ClickHouse MCP is being used at runtime, so it should not be batched at the end.

## Footage attribution

Demo dailies are cut from **Tears of Steel** © Blender Foundation, [mango.blender.org](https://mango.blender.org/),
licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
