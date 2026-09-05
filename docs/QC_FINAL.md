# QC #4 — final hosted pass (judge simulation)

**Reviewer:** final QC / judge #4. **Date:** 5 Sep 2026, 18:20–19:05 UTC.
**Build under test:** the **hosted** product only — Cloud Run `slateiq-00009` at entry,
**`slateiq-00010-6vb`** after the two fixes below. Chrome DevTools MCP at **1440×900** and **390×844**,
plus `curl` for every endpoint the browser sandbox cannot prove (downloads, cross-origin).
Ground truth re-computed against ClickHouse `:8123` directly.

Previous passes: [`QC_1.md`](QC_1.md) (UX), [`QC_2_AGENT.md`](QC_2_AGENT.md) (agent/guardrails),
[`JUDGE_REVIEW_3.md`](JUDGE_REVIEW_3.md) (full package).

---

## (a) Scorecard

| Criterion | JR#3 | **QC #4** | The one sentence |
|---|:--:|:--:|---|
| **Technological Implementation** | 5 | **5 / 5** | Eight questions asked through the hosted UI; **every one** that touched data showed `run_query` · **`via mcp-clickhouse`** · the generated SQL · a real row count in the trace panel, and the numbers matched ClickHouse when I re-ran them myself (soft-focus chip → 13 takes led by `TOS-D12-S12-B-02-B` at 13.0 s / avg 0.521; boom chip → **7**, exactly `count()` on `take_event` for day 12). `/api/health` returns `mcp:"up"`, `clickhouse:"up"`, `clickhouse_mcp_auth:true` in 0.77 s. 116 unit tests green, `db/verify.py` **43/43**. |
| **Design** | 5 | **5 / 5** | Four screens, one visual language, **zero console errors across the whole session**, and **no horizontal overflow at 390 px on any of the four screens**. Takes defaults to *"Scenes with footage (8)"* — 24/24 posters load, clips play from GCS (`readyState 4`, 1280×534). All four Grafana panels render data. The two rough edges I found were both real and both are fixed below. |
| **Potential Impact** | 4 | **4 / 5** | Unchanged, and unchanged for the reason JR#3 gave: the value is always *hours*, never *money*. The Editor's Log **CSV + ALE** export is the strongest new impact argument in the build — an ALE drops straight into a Media Composer bin, which is the difference between "interesting" and "I would use this Monday" — and nothing in the copy says so. |
| **Quality of the Idea** | 4 | **4 / 5** | Unchanged. |

**Composite: 18 / 20.** No regressions against JR#3; two new P1s found and fixed inside this pass.

---

## (b) What a judge sees in the first 60 seconds

Measured, cold tab, warm instance.

| t | What happens |
|---:|---|
| **0–2 s** | Ask screen paints. Header carries two live status dots — **MCP** and **ClickHouse**, both green. Left rail names the four screens. Footer reads *Gemini · Google ADK · **ClickHouse MCP***. The partner claim is on screen before the judge has clicked anything. |
| **2–5 s** | Seven suggested prompts, the hero one first: *"Which circled takes have more than 3 seconds of soft focus?"* The right-hand **Agent Trace** panel is already labelled *"executed against ClickHouse through the official `mcp-clickhouse` server at runtime"* while still empty. |
| **5–25 s** | Click the hero chip. The trace fills live: `Coordinator Agent · routes the question` → `transfer_to_agent {editor_agent}` → `Editor Agent` → **`run_query` `via mcp-clickhouse` · 13 rows`**, with the full SQL and `13 rows × 10 cols`. The answer leads *"We have **13 circled takes** that went soft… the absolute worst offender is **12/B/2**, 13.0 seconds, avg focus 0.521, despite the director's note saying 'Cleaner. Print.'"* Footer: `1 query · 13 rows · 20 s · through mcp-clickhouse`. |
| **25–45 s** | Second chip → three **take cards with real poster frames**; clicking one plays the clip inline from GCS. |
| **45–60 s** | Production Health: four Grafana panels with data (`-3.50` pages behind, `48.50` shot, `12.00` days), then **Generate Daily Progress Report → 0.5 s**, **Read it aloud → 1.7 s**, and two export buttons that hand over a real CSV and a real ALE. |

**The claim and the proof are the same artifact inside the first minute.** That is the whole submission,
and it lands.

*The one caveat: this is the **warm** path. A cold Cloud Run instance costs ~16 s of ADK import before
any of the above; the README states that number honestly.*

---

## (c) Issue table

| # | Sev | Area | What I saw | Status |
|:--:|:--:|---|---|---|
| **1** | **P1** | Chat error handling | A transient **Gemini 503** on *"Continuity issues in scene 41"* rendered the **raw provider JSON** into the chat window — `ServerError: 503 Service Unavailable. {'message': '{\n "error": {\n "code": 503, …` — **truncated mid-word** (`Please t)`), and then **again** in a red error box directly below it. `friendly_error()` covered MCP outages but not model-capacity errors, so a Gemini blip read as a broken product. | **Fixed** — `guardrails.friendly_error()` now maps 503 / `UNAVAILABLE` / 429 / `RESOURCE_EXHAUSTED` / *"experiencing high demand"* / *overloaded* / *rate limit* to *"The Gemini model is busy right now… nothing is wrong with the data — ask again in a few seconds."* Checked **before** the MCP hints, so a capacity blip is never mis-reported as a database outage. `Ask.tsx` suppresses `ErrorBox` when it would repeat the answer bubble. 3 regression tests added. |
| **2** | **P1** | Read aloud | **The shipped TTS cache was stale.** `data/cache/tts/` held two wavs baked against an older DPR text; the current day-12 report hashes to `250abc99…`, which was **not** in the image. So the *first* "Read it aloud" on **every fresh Cloud Run instance** cost **55.5 s** of Gemini summarisation + synthesis — and that is a beat the trailer shows on camera. Second click was 1.6 s, which is exactly why it had not been caught: it only reproduces on a cold instance. | **Fixed** — correct wav baked into `data/cache/tts/` (`.gcloudignore` already keeps that directory). Re-verified on the **new** revision: **1.71 s, `X-SlateIQ-Cached: 1`**. |
| 3 | P2 | Take gallery | *"Every take where Celia says 'forty years'"* — a suggested chip — returns 9 take cards and **all 9 read "Media not published"**, because only **24 day-12 clips** exist in GCS and that query is a deliberate cross-day dialogue search. The label is honest and the Takes screen handles this well (it defaults to *Scenes with footage (8)*), but this one chip shows a wall of grey placeholders. | **Open, accepted.** Fixing it means either publishing more footage or narrowing the chip, and narrowing it destroys the point of the question (cross-day search is the impressive part). Noted as a known cost. |
| 4 | P2 | Latency | *"Write today's Daily Progress Report"* through the **chat** takes **87 s** (13 queries, hits the 12-query budget). The Production Health **button** for the same report is **0.5 s** from cache. A judge who tries the chip instead of the button waits a minute and a half. | **Open.** The fast path is the one the trailer and the README point at; the slow one is a chip. Lowest-risk fix would be routing that chip to the cached endpoint, which is a behaviour change I would not make hours before a deadline. |
| 5 | P3 | Report API | `GET /api/report/editor-log?day=12` (uncached) takes **110 s**. | **Open, not judge-facing** — verified by grep that the UI calls only `/api/report/dpr` (cached, 0.7 s) and `/api/export/editors-log` (SQL, 0.7 s). Nothing in the product reaches this route. |
| 6 | P3 | Ask screen | After the first question the suggestion strip drops from 7 chips to 4 (`CHIPS.slice(0, 4)`). Chips 5–7 are then only reachable by typing. Deliberate, and correct for space — noting it so the next reviewer does not file it as a bug. | By design. |

**No P0s.** Nothing in the product is wrong, missing, or overstated.

---

## (d) Everything verified, with numbers

### The 7 suggested chips, one by one

Latencies are the agent time the UI itself prints. Every count re-checked against ClickHouse.

| # | Chip | Result | Correct? |
|:--:|---|---|:--:|
| 1 | Which circled takes have more than 3 s of soft focus? | `1 query · 13 rows · 20 s` — leads with `12/B/2`, 13.0 s soft, avg 0.521 | ✅ matches QC#2 ground truth exactly |
| 2 | Best takes for scene 27? | `1 query · 3 rows · 9.5 s` — 3 take cards, **posters load, clip plays** | ✅ |
| 3 | Are we on schedule after day 12? | `2 queries · 13 rows · 18 s` | ✅ leads with the **deficit** — JR#3's on-camera mismatch is closed |
| 4 | Every take where Celia says 'forty years' | `7 queries · 125 rows · 35 s` — 9 takes, days 2/5/9/12 | ✅ answer correct; see issue #3 for the posters |
| 5 | Takes with boom in shot today | `1 query · 7 rows · 12 s` | ✅ **7** = `count()` on `take_event` for day 12, verified |
| 6 | Continuity issues in scene 41 | first attempt **Gemini 503** (issue #1); retry `4 queries · 96 rows · 19 s`; post-deploy `9 queries · 79 rows · 36 s` with 3 playable take cards | ✅ on every non-503 run |
| 7 | Write today's Daily Progress Report | `13 queries · 48 rows · 87 s` | ✅ correct, slow — issue #4 |

**Trace correctness: 7/7.** Every data-touching answer showed the coordinator hand-off, the named
specialist, `run_query` tagged **`via mcp-clickhouse`**, the SQL, and a row count. On the 503 the
footer correctly read `0 queries · 0 rows` and **dropped** the `through mcp-clickhouse` chip — JR#2 #13
holding up under a real failure.

### Screens

| Screen | 1440×900 | 390×844 |
|---|---|---|
| Ask | ✅ 7 chips, live trace panel, take gallery | ✅ nav becomes a scrollable tab bar, chips wrap, no overflow |
| Takes | ✅ defaults to *Scenes with footage (8)*, **24 takes, 24/24 posters**, filters (All/Circled/NG/Hold), counts `9 circled · 6 NG · 5 hold` | ✅ |
| Production Health | ✅ **4/4 Grafana panels with data**; print-ratio panel is `LIMIT 10` (JR#3 P3 closed); *Scenes at risk* renders all 5 columns with **eighths** (`4/8`, `5/8`) | ✅ |
| About | ✅ **8/8 external links resolve 200** (repo ×2, app, Grafana, MCP `/health`, mango.blender.org ×2, CC BY 3.0) | ✅ |

`document.scrollWidth === clientWidth === 390` on all four. **0 console errors, 0 failed requests** for
the entire session.

### Editor's Log export (new in sprint 4)

Both are `<a href>` links, so the DevTools sandbox will not save the file — verified by `curl` instead.

| Format | Response | Content |
|---|---|---|
| CSV | **200**, `text/csv; charset=utf-8`, `content-disposition: attachment; filename="slateiq_editors_log_day12.csv"`, 11 856 B, 0.70 s | Header `Scene,Slug,Shot,Take,Camera,Camroll,Soundroll,TC In,TC Out,Duration (s),Status,Director note,Gemini summary,Quality,Flags,Take ID,Clip`; embedded commas and newlines correctly quoted |
| ALE | **200**, `text/plain`, `filename="slateiq_editors_log_day12.ale"`, 9 320 B, 0.69 s | Valid 3-section Avid Log Exchange — `Heading` (`FIELD_DELIM TABS`, `VIDEO_FORMAT 1080`, `AUDIO_FORMAT 48khz`, `FPS 25`), `Column`, `Data`; rows like `6/A/6-A  V A1A2  08:11:36:04  08:12:25:03  00:00:48:24 …` |

### DPR + Read aloud

| Action | Cold instance (rev 00010) | Warm |
|---|---|---|
| Generate Daily Progress Report (day 12) | **0.70 s** | 0.4 s |
| Read it aloud | **1.71 s**, `X-SlateIQ-Cached: 1`, 39.3 s of audio, plays | 1.6 s |

The DPR cumulative line now reads **`pages shot 48 4/8 of 52 planned to date — behind by 3 4/8 · 115 3/8 total script`** — JR#3 open item #5 / JR#2 #9 **closed**, denominators no longer mixed.

### Repo, licence, secrets

| Check | Result |
|---|---|
| `git grep -nE "AIza\|AQ\.Ab8\|gho_\|BEGIN PRIVATE"` | **empty** ✅ |
| `.env` / `.secrets/` tracked? | **no** — `git ls-files` matches nothing; both in `.gitignore` ✅ |
| Licence | **Apache-2.0**, recognised by GitHub, `LICENSE` resolves 200 ✅ |
| Homepage | set to the Cloud Run URL ✅ · description set · 6 topics (`clickhouse`, `film-production`, `gemini`, `google-adk`, `hackathon`, `mcp`) ✅ |
| README on GitHub | renders; **4/4 images 200 `image/png`** from `raw.githubusercontent.com`; **mermaid fence renders** (GitHub emits its `data-type="mermaid"` container); **every relative link resolves** ✅ |
| Only Google AI | `git grep -niE "openai\|anthropic\|claude\|mistral\|llama" -- ':!docs' ':!*.md'` → **2 hits, both comments**: `ingest/gemini.py:3` *"Only Google AI is used in SlateIQ product code (see CLAUDE.md)"* and `ingest/load.py:16` *"Direct clickhouse-connect is used here on purpose — CLAUDE.md allows it for…"*. Both are the word **CLAUDE.md** (the repo's own instruction file) in a comment. **No non-Google model API anywhere in the product.** ✅ |

### Local suites

| Suite | Result |
|---|---|
| `python -m pytest agent/tests -q` | **116 passed** in 1.5 s (113 + 3 added this pass) |
| `python db/verify.py` | **43/43 passed** — 2 503 takes · 66 continuity notes · **3 074 957** telemetry rows · 12 daily-agg · all 15 golden queries return rows |

---

## (e) What changed in this pass

Commit `eeadae9`, Cloud Run **`slateiq-00010-6vb`**.

| File | Change |
|---|---|
| `agent/slateiq_agent/guardrails.py` | `_MODEL_BUSY_HINTS` + `_FRIENDLY_MODEL_BUSY`; `friendly_error()` checks model capacity **before** MCP hints |
| `agent/tests/test_guardrails.py` | 3 tests: a Gemini 503 never leaks the payload and never blames MCP; a 429 is also "busy"; an MCP outage still reports the database |
| `web/src/screens/Ask.tsx` | `ErrorBox` only renders when it says something the answer bubble does not |
| `data/cache/tts/250abc99….wav` | the day-12 DPR read-aloud, baked so a cold instance is instant |
| `web/dist/` | rebuilt |

---

## (f) Remaining risks

Ordered by what would actually cost a point.

1. **The video is still not uploaded.** `video/slateiq_trailer_720p.mp4` is committed and QC'd, but the README Live table and `docs/SUBMISSION.md` still say *uploading*. This is the only genuine hole in the package and it needs a human with a YouTube account. Everything else on this page is polish.
2. **Cold start ~16 s.** `min-instances` is 0 on purpose. A judge who is the first visitor in an hour waits 16 s on a blank-ish screen before the Ask screen paints. The README says so honestly; nothing else mitigates it. **If there is budget for one thing on submission day, set `min-instances=1` for the judging window.**
3. **Gemini capacity.** I hit a real 503 in an eight-question session. It now degrades to a clean *"the model is busy, ask again"* instead of raw JSON — but a judge who hits it still sees a non-answer. Nothing more can be done from our side.
4. **Media coverage.** 24 clips exist for 2 503 takes. The product is honest about it everywhere and the Takes screen defaults around it, but one suggested chip (#3 above) shows nine empty cards.
5. **The DPR chat chip is 87 s** (#4). The button is 0.5 s. A judge who picks the chip forms a slow impression of a fast product.
6. **Impact is still priced in hours, not money** — JR#3's item #6, unchanged. One clause (*"a reshoot day on a mid-budget feature is $80–150 k"*) in the README and Devpost "What it does" is the cheapest available point in the whole submission.
7. **Single-region, single-VM MCP.** `35.239.36.85` is one e2-micro. It has a systemd unit and restart policies and survived a reboot in 103 s, but if it is down during judging, every analytical answer degrades to the friendly MCP message.
