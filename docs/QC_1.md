# QC pass #1 — product / UX, driven through the real UI

**Reviewer:** QC lead #1, acting as a hackathon judge who is also a film editor / 1st AD.
**Date:** 5 Sep 2026 · **Build under test:** local stack — FastAPI+ADK on `:8811`, `mcp-clickhouse` on `:8765`,
ClickHouse 25.6 on `:8123`, `web/dist` served at `/`. Chrome DevTools MCP at 1440×900 and 390×844.

Everything below was found by driving the actual UI and checking every number the agent said against
ClickHouse over HTTP. **All P0 and P1 issues in this table have been fixed and re-verified**; the fixes
are in this same commit.

---

## Issues

| # | Sev | Area | Repro | Expected | Actual | Fix | File |
|:--:|:--:|---|---|---|---|---|---|
| 1 | **P0** | Takes screen | Click **Takes** in the rail | Grid of take cards | **Whole app goes blank.** `Uncaught TypeError: (a ?? []) is not iterable`. Header, nav and health dots die with it; a hash change does not recover it, only a reload. | `/api/takes` returns `{count, source, takes:[…]}` but `getTakes` was typed/parsed as a bare `Take[]`. Normalise both shapes in `api.ts` (`unwrapList`). | `web/src/lib/api.ts` |
| 2 | **P0** | Production Health | Click **Production Health** | 4 charts + DPR panel | **Blank screen**, `TypeError: e is not iterable` — same root cause as #1. | Same normaliser; both screens now render. | `web/src/lib/api.ts` |
| 3 | **P0** | Ask · take cards | Ask "Best takes for scene 27 and why?" | Cards reading `27/A/1 · CIRCLED` | Every card read **`SC undefined-undefined`** and **`UNKNOWN`** — on the demo's money shot. | Two contracts disagreed: the agents emit `{take_id, clip_uri, t, label, reason}`, the cards need `scene_number/shot/take_number/status`. `/api/chat` now **enriches** each cited take from ClickHouse before the `final` event (same non-reasoning listing path as `/api/takes`), the UI prefers `final.takes` over re-parsing the model's fenced block, and `takeLabel()` falls back to parsing the slate out of `take_id`. | `agent/main.py`, `web/src/screens/Ask.tsx`, `web/src/lib/media.ts`, `web/src/lib/types.ts` |
| 4 | **P0** | Resilience | Any screen throwing | The other screens keep working | One bad API shape blanked the entire SPA (#1/#2) because there was no error boundary. | Added `ErrorBoundary` around the screen slot, with a retry that clears on route change. | `web/src/components/ErrorBoundary.tsx`, `web/src/App.tsx` |
| 5 | **P1** | Header health dots | Load any screen | Green MCP + ClickHouse dots — this is Stage-1 partner evidence on screen | Both dots **permanently grey/"unknown"**. `/api/health` never returned `mcp` / `clickhouse` at all, although the UI (and `web/README.md`) documented them. | `/api/health` now probes the mcp-clickhouse `/health` route and runs `SELECT 1`, returning `{ok, mcp, clickhouse}`. | `agent/main.py` |
| 6 | **P1** | Agent trace | Ask anything, watch the trace | Real row counts | **Every query reported "1 rows"**, regardless of the real result, and hand-offs reported **"-1 rows"**. The panel header summed those, so "16 rows" for a 19-query run. A judge checking the trace against the answer sees a lie. | The row counter matched the FastMCP `content[]` envelope (always length 1). Unwrap `content[].text` / `structuredContent.result` and count the real `rows`; render a readable `3 rows × 9 cols (take_id, shot, …)` summary instead of dumping the raw envelope; header ignores negatives. | `agent/slateiq_agent/runtime.py`, `web/src/components/AgentTrace.tsx` |
| 7 | **P1** | Agent trace | Ask anything | ADK's own routing call is not a partner call | `transfer_to_agent` was labelled **"MCP CALL"** — overstating the ClickHouse-MCP evidence in the one panel that exists to prove it. | Only `run_query` / `list_tables` / `list_databases` / `describe_table` are labelled `MCP call`; routing is labelled `ADK routing`, its row chip and its `null` result are hidden. | `web/src/components/AgentTrace.tsx` |
| 8 | **P1** | Media | Takes gallery, and take cards in chat | Thumbnails | **Zero thumbnails anywhere** — 76 of 91 image requests 404. `thumb_uri` is `thumbs/<id>.jpg` but nothing was mounted at `/thumbs`; the fallback then guessed `/clips/<id>.jpg`, also 404. The 24 poster frames existed on disk the whole time. | Mounted `data/thumbs` at `/thumbs` (`THUMBS_DIR` overridable). | `agent/main.py` |
| 9 | **P1** | Ask · take cards | Ask a question that cites takes | Poster frame on each card | Cards stayed on the striped placeholder even after the fix above: during streaming the take is known only by `take_id`, the guessed poster 404s, and the `broken` flag was never reset when the real `thumb_uri` arrived. | Reset the broken flag when the resolved thumbnail URL changes. | `web/src/components/TakeCard.tsx` |
| 10 | **P1** | Takes drawer | Open any take → *Transcript & flag timeline* | Timestamped dialogue + clickable flag timeline | **Always "No event detail for this take."** `/api/take/<id>/events` returns `{take, events:[{t_offset_s, flag_type, …}], …}`; the client demanded a bare array of `{t, flag}` and silently returned `null`. A headline feature was dead. | Normalise the wrapper and the ClickHouse column names in `getTakeEvents`. | `web/src/lib/api.ts` |
| 11 | **P1** | Takes gallery | Open **Takes** | Takes you can actually play | Default listing was ordered `day_number ASC`, so the first 100 cards were day-1 synthetic takes with `gs://` URIs and no media on this box. | Order the gallery by local-media-first, then newest shooting day. | `agent/main.py` |
| 12 | **P1** | Terminology | Production Health, 4th chart | Judge review #1 item 5 | Chart still titled **"Shooting ratio by scene"** while plotting takes-per-circled-take. A 1st AD spots this instantly and it devalues every other correct term in the product. | Renamed to **Print ratio by scene**, with a one-line note saying what the shooting ratio actually is. Same rename in the `VITE_GRAFANA_PANELS` default. | `web/src/screens/Health.tsx` |
| 13 | **P1** | DPR content | `GET /api/report/dpr?day=12` | Both ratios, correctly named | The report agent dropped print ratio and printed the takes-per-print figure under **"Shooting ratio: 4.6:1"** — the exact error the template was written to avoid. | Hard rule in `report_instruction()`: the totals line must carry both, with the duration-based formula spelled out. Now emits `Print ratio: 4.61:1 · Shooting ratio: 4.44:1`. | `agent/slateiq_agent/prompts.py` |
| 14 | **P1** | DPR latency | Click **Generate Daily Progress Report** | A report before the judge leaves | **5m28s** on the first measurement (later 2m46s), with a static skeleton and no sign of life. | On-disk report cache (`data/cache/reports/`, the same policy as the ingest cache) → **10 ms** on repeat, `?refresh=1` to regenerate; plus a running `Generating… Ns` clock and a line explaining the round trips. Day 12 is pre-warmed and committed. | `agent/main.py`, `web/src/screens/Health.tsx` |
| 15 | **P2** | SQL disclosure | Ask anything | "SQL run through MCP (n)" matches the trace | Disclosure said **(1)** while the trace showed 5 — it used the model's *claimed* SQL list. | `final.sql` is now the SQL actually observed going through MCP; the claimed list is only a fallback. | `agent/slateiq_agent/runtime.py` |
| 16 | **P2** | TTS latency | **Read it aloud** | Audio | 56–74 s of silence (Gemini summarise + TTS), every single time. | Disk cache keyed on model+voice+text → **6 ms** on repeat. | `agent/main.py` |
| 17 | **P2** | Trace labels | Ask anything | "Coordinator agent" | Chip read **"Slateiq Coordinator Agent"** (ADK reports the registered name) and printed a bare `null` under the hand-off. | Mapped `slateiq_coordinator`; suppressed `null` summaries. | `web/src/components/AgentTrace.tsx` |
| 18 | **P2** | Takes drawer | Open a take in scene 102 | Unambiguous slate | Title read **"Scene 102A — Take 1"**, which reads as scene 102A — and `14A` *is* a real scene number in this show. | Now `Scene 102 · Shot A · Take 1`. | `web/src/screens/Takes.tsx` |
| 19 | **P2** | Types | — | `scene_number` is a string (`14A`) | Typed `number` throughout; the scene dropdown sorted with `a - b` (NaN) and the filter coerced to `Number`. | Strings end-to-end, natural-order sort. | `web/src/lib/api.ts`, `web/src/screens/Takes.tsx`, `web/src/screens/Health.tsx` |
| 20 | **P2** | Copy | Kill the backend, load the UI | Correct port | Error read "Is the backend running on **:8080**?" — 8080 is another app on this box; SlateIQ is 8811. | Port-agnostic wording. | `web/src/lib/api.ts` |
| 21 | **P2** | Docs | Read `web/README.md` | The contract the backend actually serves | Three endpoint shapes were documented wrong (`/api/takes`, `/api/take/<id>/events`, the structured take block) and `/thumbs` was missing — which is how #1, #2, #3 and #10 happened. | README rewritten against the live API, including the `rows` / non-query-tool rule. | `web/README.md` |

### Open (not fixed — deliberately out of scope for this pass)

| Sev | Item | Note |
|:--:|---|---|
| P2 | Cold "are we on schedule" runs long — **124 s / 19 queries** | Correct, and impressively thorough, but the longest wait in the demo. Worth a query budget on `production_agent` like the one the report agent has. |
| P2 | The ~76 synthetic takes per page still point at `gs://slateiq-dailies/…` | They degrade to the striped placeholder and, because they are lazy-loaded, never even fire a request in the viewport. Real fix belongs to deploy: make the bucket public or upload posters. |
| P2 | Long SQL in the trace clips at the panel edge | It scrolls horizontally, but there is no affordance saying so. |
| P2 | About page has no repo / hosted URL and no screenshots | Judge review #1 item 10. The images this pass produced (`docs/img/*.png`) are now available for it and for the root README. |

---

## What worked — and it is a lot

**Answer quality is the strongest part of this product. Nine questions, zero hallucinated numbers.**
Every figure below was re-checked against ClickHouse directly over `:8123`.

| Question | Latency | Verdict |
|---|--:|---|
| Best takes for scene 27 and why? | 19–23 s | ✅ All 3 takes, right statuses, right quality scores, correctly named the sound-clip flag at 5.0 s on the NG take and told the editor they'd be committing to ADR. |
| Are we on schedule after day 12? | 124 s, 19 queries | ✅ 52 pages planned / 48 4/8 shot / **3 4/8 behind** — exact. Traced the entire deficit to the rain days 8 and 11 (14 eighths each — verified), 22.2 setups/day, 9.4 takes per setup, 66 7/8 pages unshot, 16.5 days needed against 18 remaining. Named print ratio and shooting ratio separately and correctly. It also recovered from a bad column guess by issuing `DESCRIBE TABLE`. |
| Every take where Celia says 'robot hand' | 26–30 s | ✅ Exactly the 2 takes, both at 5.3 s. First query used `speaker = 'Celia'`, got 0 rows against `CELIA`, and recovered with `ILIKE` — visible in the trace, and honest. |
| Which takes today have boom in shot or soft focus? | 19 s | ✅ **18 takes** — matches `uniqExact` exactly — with all five severity-5 offenders listed with the right flag, timestamp and severity. |
| Any continuity issues in scene 33? | 40 s | ✅ All three severity-5 notes (props / action match / dialogue) between the circled `33/A/1` and the pending `33/B/1`, with the actual conflicting props and lines, and a pick-up-or-cut-around recommendation. |
| Write today's Daily Progress Report | 166 s cold / 10 ms cached | ✅ Correct industry format, per-scene table, both ratios named correctly after the fix, eighths rendered right (`8/8` prints as `1 page`). |
| "drop table take" | 9 s | ✅ Refused, explained read-only, offered three real questions. Never reached a tool. |
| "what's the weather in Paris" | 8 s | ✅ Declined, in character, redirected — and correctly noted the shoot is in Amsterdam. |
| "how did today go?" (ambiguous) | 63 s | ✅ Read it as day 12 and answered as a producer would: pages, setups, both ratios, the overtime trend against days 8 and 11, the four rain-dropped scenes with page counts, and the severity-5 continuity conflicts. Every number checked out. |

Also good:

- **The trace panel is the best partner evidence I have seen in a hackathon UI** — sub-agent hand-off, tool name, syntax-highlighted SQL, copy button, row count, and the `LIMIT` the guardrail appended, all streaming live. After the fixes, the numbers in it are true.
- **Routing is right every time.** Coordinator → editor / production / continuity / report, visible on screen.
- **The guardrail is visible working**: a query written without a `LIMIT` shows up in the trace with `LIMIT 100` appended.
- **Take cards seek to the cited timestamp.** `12/A/1 @00:05` opens the real clip at 5.3 s; `readyState 4`, no media errors.
- **The drawer's flag timeline** is genuinely useful once it renders — clickable dialogue/flag markers that scrub the player.
- **Design holds up.** Dark cutting-room palette, correct crew vocabulary throughout (circled, NG, hold, wild, setups, slate, print), the clapper motif, and an About page whose architecture diagram is accurate rather than decorative.
- **Mobile (390 px):** all four screens render, no horizontal overflow anywhere, the trace panel collapses into a "View agent trace (n)" disclosure. Clean pass.
- **Final sweep: 0 console errors, 0 failed network requests across all four screens.**

Screenshots from the fixed build: `docs/img/ask.png`, `trace.png`, `takes.png`, `health.png`, `dpr.png`, `about.png`.
