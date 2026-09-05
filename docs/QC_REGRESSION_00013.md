# Regression pass — Cloud Run rev `slateiq-00013-qvp`

**What changed under test:** the cached-report `FunctionTool` (`get_cached_report` on
`report_agent`) plus the `[[SLATEIQ_CACHED_REPORT]]` marker splicing in
`runtime.stream_agent` — i.e. the **streaming path**. This pass re-runs the
[`QC_FINAL.md`](QC_FINAL.md) checklist against the hosted product to prove nothing
regressed around it.

**Where:** `https://slateiq-957930801789.us-central1.run.app`, Chrome DevTools MCP at
1440×900 (and 390×844 for the overflow pass), plus `curl` for the endpoints the browser
sandbox cannot prove. **Date:** 5 Sep 2026, ~21:05-21:40 UTC+10. Warm instance
(Cloud Scheduler keep-warm is live).

**Verdict: no P0. No code changed.** Two P2s recorded below, both new, neither
judge-facing on a fresh instance.

---

## Results

| # | Check | Result | Latency |
|:--:|---|---|---|
| 1 | `/api/health` | 200, `mcp:up` · `clickhouse:up` | **0.68 s** |
| 2 | Chip 1 — circled takes >3 s soft focus | ✅ text streams; coordinator → **Editor Agent** → `run_query` **via mcp-clickhouse**; 13 rows; leads `12/B/2` 13.0 s / avg 0.521; 12 take cards | 25 s · 1 query · 13 rows |
| 3 | Chip 2 — best takes for scene 27 | ✅ Editor Agent · `run_query` via mcp-clickhouse; **3 take cards, posters render** | 8.9 s · 1 query · 3 rows |
| 4 | Chip 3 — on schedule after day 12 | ✅ coordinator → **Production Agent** → 5× `run_query` via mcp-clickhouse | 27 s · 5 queries · 19 rows |
| 5 | Chip 4 — where Celia mentions her robot hand | ✅ coordinator → Editor Agent → `run_query` via mcp-clickhouse; **2 take cards @00:05, posters render** | 16 s · 3 queries · 6 rows |
| 6 | Chip 5 — takes with boom in shot today | ✅ `run_query` via mcp-clickhouse; **7** takes (matches `take_event` day-12 ground truth); 7 cards | 11 s · 1 query · 7 rows |
| 7 | Chip 6 — continuity issues in scene 41 | ✅ coordinator → **Continuity Agent** → 6× `run_query` via mcp-clickhouse; 3 take cards | 26 s · 6 queries · 63 rows |
| 8 | Chip 7 — **Write today's Daily Progress Report** | ✅ coordinator → **Report Agent** → `get_cached_report {kind:dpr, day:12}` labelled **`report cache · local file`**; footer `0 queries · 0 rows`; full DPR rendered; closes `Cached report generated at 2026-09-05T07:36:45+00:00; say "refresh" to regenerate.` | **6.6 s** (target <15 s) |
| 9 | **No marker / raw-JSON leak** | ✅ `[[SLATEIQ_CACHED_REPORT]]` never appears in the visible text on any of the 8 turns; no `ServerError` / provider JSON / tool-result JSON in the answer bubbles (the trace panel shows the tool result, as designed) | — |
| 10 | **"Refresh today's Daily Progress Report"** | ✅ regenerates live — **13 `run_query` calls** via mcp-clickhouse, no `report cache` chip, no cached-at line, no marker leak | 93 s · 13 queries · 132 rows |
| 11 | Production Health — Generate DPR button | ✅ full report renders | **~0.5 s** |
| 12 | Production Health — Read it aloud | ✅ plays, `readyState 4`, 36 s of audio — but **first click cost 60.5 s** (see P2-b); second click cached | 60.5 s / **0.50 s** |
| 13 | Export Editor's Log (CSV) | ✅ 200 `text/csv`, `attachment; filename="slateiq_editors_log_day12.csv"`, 11 856 B, 38 rows, header + quoting correct | 0.74 s |
| 14 | Export Editor's Log (ALE) | ✅ 200 `text/plain`, valid `Heading/Column/Data` (`FIELD_DELIM TABS`, `VIDEO_FORMAT 1080`, `FPS 25`), 9 320 B, 38 rows | 1.19 s |
| 15 | Grafana iframes (4) | ✅ **4/4 render with data** — `-3.50` behind / `48.50` shot / `12.00` days; pages planned-vs-shot series draws; print ratio; *Scenes at risk* all 7 columns with eighths (verified in the solo panel; the embed clips the last two columns horizontally at 1440 — cosmetic, pre-existing) | ~6 s first paint |
| 16 | `GET /api/report/editor-log?day=12` | ⚠️ **first hit 99.6 s, `cached:false`** — the baked `editor_log_day12.json` is *not* in the rev-00013 image (see P2-a). Every hit after that 0.65–0.74 s, `cached:true` | **99.6 s** → 0.65 s |
| 17 | Takes gallery | ✅ defaults to *Scenes with footage (8)*, `9 circled · 6 NG · 5 hold`, 24 takes; 20/24 posters decoded in-viewport (the other 4 are `loading="lazy"` below the fold); **clip plays** `readyState 4`, 1280×534, unpaused, from GCS | — |
| 18 | About — external links | ✅ 8 links / 6 unique hosts, **all 200** (repo, app, Grafana, MCP `/health`, mango.blender.org, CC BY 3.0) | 0.6–2.1 s |
| 19 | Console | ✅ **0 errors from the SlateIQ origin.** 9 messages total, all from the embedded **Grafana** iframes (4× unknown-plugin preload, 2 translation warns, 3 `Error loading dashboard: Failed to fetch` from iframes torn down mid-load by the 390 px route sweep) | — |
| 20 | 390×844 overflow | ✅ `scrollWidth === clientWidth === body.scrollWidth === 390` on **all four** screens | — |
| 21 | `python -m pytest agent/tests -q` | ✅ **126 passed** | 1.6 s |

---

## Issues found (both new, both P2, no fix applied)

**P2-a — the baked Editor's Log is missing from the deployed image.**
`data/cache/reports/editor_log_day12.json` is tracked, valid (6 579 chars) and *not*
`.gcloudignore`d, but the first hosted call to `/api/report/editor-log?day=12` returned
`cached:false` and rebuilt the document live in **99.6 s / 13 queries**. So rev 00013's
image does not carry the file that commit `eb10466` baked — the deploy and that commit
crossed. **Not judge-facing:** nothing in the UI calls this route (QC#4 #5 still holds —
the UI uses `/api/report/dpr` and `/api/export/editors-log`), the DPR bake *is* in the
image (chip 7 served `generated_at 07:36:45` straight from it), and the instance is warm
now. A plain redeploy would close it; not worth the churn on its own.

**P2-b — a chat "refresh" invalidates the pre-warmed TTS wav on that instance.**
The new write-back callback overwrites `dpr_day12.json` with the regenerated report, so
the DPR text no longer hashes to the wav baked into `data/cache/tts/` and the next
*Read it aloud* pays full Gemini summarise+synthesise — **60.5 s**, measured. QC#4 #2
fixed exactly this shape of bug for cold instances; the refresh path re-opens it for the
life of one instance. A judge who does not type "refresh" never sees it (the button is
1.7 s cold, as QC#4 measured), and the next instance starts from the image again.
Recorded, not fixed, hours from the deadline.

## What did **not** regress

Every finding QC#4 closed is still closed: no raw provider JSON in chat, the DPR button
is sub-second, all four Grafana panels carry data, `Scenes at risk` shows eighths, both
exports are real files, 390 px is clean on all four screens, and every data-touching
answer still shows the coordinator hand-off, the named specialist, `run_query` tagged
**via mcp-clickhouse**, the SQL and a row count. The one genuinely new surface — the
cached-report tool — behaves exactly as specified: `report cache · local file`, never
`via mcp-clickhouse`, marker spliced invisibly, and "refresh" still goes to the database.
