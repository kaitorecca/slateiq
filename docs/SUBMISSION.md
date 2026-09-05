# Submission checklist — Agentic Cinema (ClickHouse track)
Deadline: 9 Sep 2026 14:00 PDT = 10 Sep 07:00 AEST.

Status re-verified on the hosted product **5 Sep 2026 18:20–19:05 UTC** against Cloud Run
**`slateiq-00010-6vb`** — hosted URLs only, no local stack. Front-end a11y/SEO fixes and the
repo-hygiene pass then shipped as **`slateiq-00011-qzd`** (`/api/health` re-checked: `mcp:"up"`,
`clickhouse:"up"`). Trailer **v2** rendered and committed the same evening.
Evidence and repro for every line: [`QC_FINAL.md`](QC_FINAL.md) (latest) · [`JUDGE_REVIEW_3.md`](JUDGE_REVIEW_3.md) · [`JUDGE_REVIEW_2.md`](JUDGE_REVIEW_2.md).

| Item | Requirement | Status | Where |
|---|---|---|---|
| Partner track | ClickHouse — official `mcp-clickhouse` used at runtime | ✅ **verified live** — `/api/health` returns `mcp:"up"`; 4 hosted questions each streamed `run_query` · `via mcp-clickhouse` · SQL · real row counts; endpoint returns 401 without bearer | https://slateiq-957930801789.us-central1.run.app/api/health · https://35.239.36.85.sslip.io/health |
| Google Cloud | Gemini (google-genai/ADK), Cloud Run, GCS, Secret Manager | ✅ **verified live** — `gemini-3.5-flash` + `gemini-2.5-flash-preview-tts` reported by `/api/health`; two Cloud Run services; public GCS bucket (48 objects, `access-control-allow-origin: *`); 2 Secret Manager secrets | deploy/OUTPUT.md |
| Hosted URL | public, testable by judges | ✅ **200, no auth** — **QC #4: all 7 suggested chips run end to end** (9.5 s / 12 s / 18 s / 20 s / 19 s / 35 s / 87 s), every data answer traced through `run_query · via mcp-clickhouse`, counts re-checked against ClickHouse; **0 console errors, 0 failed requests**; **no horizontal overflow at 390 px on any of the 4 screens** | https://slateiq-957930801789.us-central1.run.app |
| — Grafana dashboard | anonymous, embeddable, data in every panel | ✅ **8/8 panels return data, 0 "No data"**, anonymous Viewer, cross-origin iframe loads | https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health |
| — Clips + thumbnails in the hosted UI | takes play, posters render | ✅ **fixed & verified 5 Sep 16:37 UTC** — the server rewrites relative `clip_uri`/`thumb_uri` to `$CLIPS_BASE_URL` at response time, so `/api/takes?scene=27` returns `https://storage.googleapis.com/…` (clip `200 video/mp4`, thumb `200 image/jpeg`). Hosted Takes: **24/24 posters load, a clip plays inline** (1280×534, `readyState 4`), 0 console errors. `data/thumbs` is also baked into the image; `/thumbs/*` now 404s honestly instead of returning the SPA HTML | docs/img/takes.png |
| — Grafana embedded in the product | Production Health shows the panels | ✅ **fixed & verified** — new `GET /api/config` hands the static build the server env at boot, so the screen embeds four `d-solo` iframes on the real UID `slateiq-prod-health` with the real panel ids/titles (2 Schedule position · 1 Pages planned vs shot · 3 Print ratio by scene · 8 Scenes at risk), pinned to the shoot's time range. Grafana's own title bar is clipped so the title is not printed twice | docs/img/health.png |
| Public repo | GitHub, complete source + run instructions | ✅ public, description set, all relative links resolve, screenshots load (`200 image/png` from raw.githubusercontent), mermaid renders. **No secrets committed** — `git grep -nE 'AIza\|AQ\.Ab8\|gho_\|BEGIN PRIVATE'` empty; `.env` / `.secrets/` untracked and gitignored | https://github.com/kaitorecca/slateiq |
| — README live URLs | hosted URL above the fold | ✅ **fixed** — Live table and the reproduce-it curl carry the real URLs; repo `homepage` set to the Cloud Run URL and 6 topics added (`gemini`, `google-adk`, `clickhouse`, `mcp`, `hackathon`, `film-production`) | README.md |
| — README eval numbers | match the linked artifact | ✅ **fixed** — README now states the committed 28-question run: **28/28 reached `run_query`, 27/28 routed, judge mean 4.82/5, median latency 27.3 s**. No partial run was committed | agent/evals/last_run.md |
| License | OSI license file visible in About | ✅ **Apache-2.0** — GitHub sidebar + About screen | https://github.com/kaitorecca/slateiq/blob/main/LICENSE |
| — Test suites | agent unit tests + data verification | ✅ `pytest agent/tests` **116 passed**; `python db/verify.py` **43/43** (2,503 takes · 66 continuity notes · 3,074,957 telemetry rows · 15/15 golden queries) | agent/tests · db/verify.py |
| Footage attribution | *Tears of Steel* CC BY 3.0 | ✅ in README and on the hosted About screen, with links to mango.blender.org and the licence | About screen |
| Video | ≤ 3 min, YouTube/Vimeo public, English | ⚠️ **v2 rendered, QC'd and committed — NOT yet uploaded.** `video/slateiq_trailer_720p.mp4`, **2:56.1** (ceiling 3:00), 720p, 9.3 MB, English VO + burned captions + sidecar `CAPTIONS.srt`; `video/qc.py` **7/7 PASS**. v2 closed all three JR#3 trailer defects: 6 s cold open (the 65 ms benchmark, the full-frame `mcp-clickhouse` trace, the soft take) before a word is spoken; `b05` re-recorded so the VO and the on-screen headline agree on the schedule; a Benchmark subtitle on the terminal card naming MCP as the agent's path. **The one thing left in the entire package is a human with a YouTube account** — see [`HANDOFF.md`](HANDOFF.md) | video/slateiq_trailer_720p.mp4 · [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| Text description | features, tech, data sources, learnings | ✅ **written and final** — paste `## Inspiration` → `## Credits & licence` into the Devpost description box; two `VIDEO_URL` placeholders fill in once the video is up | docs/DEVPOST.md |
| Devpost form | fields, tags, partner track, links | ⚠️ **not yet filled** — every field is pre-written, field by field, in [`HANDOFF.md` §C](HANDOFF.md); needs a human to paste it in and press **Submit** | docs/HANDOFF.md |
| Only Google AI | no non-Google model APIs in product | ✅ **re-verified after the final commit (QC #4)** — `git grep -niE 'openai\|anthropic\|claude\|mistral\|llama' -- ':!docs' ':!*.md'` → **2 hits, both comments** (`ingest/gemini.py:3`, `ingest/load.py:16`) naming the repo's own `CLAUDE.md`. No non-Google model API on any path. | QC_FINAL.md §d |
| Newly created | during 27 Jul–9 Sep 2026 | ✅ | git history |
| Team ≤ 4 | | ✅ | solo |

## Open risks

- **Cold start measured: ~16 s.** Cloud Run logs, instance start → `Application startup complete`,
  is 15.7 s; it is the ADK import, not the database. Warm requests are ~0.6 s. `min-instances`
  stays 0 because an idle instance costs money and the free tier is the whole point; the README
  states the real number rather than the old "3–5 s" guess.
- **First DPR is now 0.7 s** — `data/cache/reports` and `data/cache/tts` ship in the image, so
  day 12's report and its read-aloud are served from the pre-warmed cache (was ~200 s).

## QC #4 — final hosted pass (5 Sep, rev `slateiq-00010-6vb`)

Full write-up: [`QC_FINAL.md`](QC_FINAL.md). **Composite 18/20, no P0s.** Two P1s found and fixed
inside the pass, then re-verified hosted:

- **A Gemini 503 leaked raw provider JSON into the chat window**, truncated mid-word and printed
  twice. `friendly_error()` now translates model-capacity errors (503 / 429 / "high demand") into a
  plain *"the model is busy, ask again"*, checked ahead of the MCP hints so a capacity blip is never
  reported as a database outage; the duplicate error box is gone. 3 regression tests added.
- **The shipped TTS cache was stale**, so the first *"Read it aloud"* on **every fresh Cloud Run
  instance** cost **55 s**. The correct day-12 wav is now baked — re-measured on the new revision at
  **1.71 s, `X-SlateIQ-Cached: 1`**.

Also confirmed closed: the DPR cumulative line no longer mixes denominators
(`48 4/8 of 52 planned to date — behind by 3 4/8`, JR#3 #5 / JR#2 #9), the schedule answer leads with
the deficit (JR#3 trailer P0), and the Grafana print-ratio panel is `LIMIT 10`.

**Top three remaining risks:** (1) the video is not uploaded; (2) ~16 s cold start with
`min-instances=0` — worth setting to 1 for the judging window; (3) impact is still priced in hours,
never money.

---

## Where the package stands — 5 Sep 2026, after the final commit

**Built, deployed, tested, committed. Two manual steps left, both of them clerical.**

| | |
|---|---|
| ✅ Product | Cloud Run rev `slateiq-00011-qzd`, `mcp:"up"` / `clickhouse:"up"`, 7/7 suggested chips traced through `run_query` |
| ✅ Data plane | e2-micro + ClickHouse + `mcp-clickhouse` 0.6.0 + Caddy; `deploy/vm/healthcheck.sh` all green |
| ✅ Tests | `pytest agent/tests` 116/116 · `db/verify.py` 43/43 · `ruff check` clean · `tsc --noEmit` clean |
| ✅ Evals | 28/28 reached `run_query` via MCP · 27/28 routed as expected · judge mean 4.82/5 |
| ✅ Lighthouse | A11y 100 · Best-practices 100 · SEO 100 · Agentic browsing 100 · LCP 522 ms · CLS 0.00 |
| ✅ Repo | public, Apache-2.0, README live URLs, screenshots, mermaid, no secrets committed |
| ✅ Video | **v2 rendered and committed** — 2:56.1, qc 7/7, all three JR#3 trailer defects closed |
| ⚠️ **YouTube upload** | **manual.** File, title, description, tags, subtitle track: [`HANDOFF.md` §A](HANDOFF.md) |
| ⚠️ **Devpost form** | **manual.** Field-by-field copy: [`HANDOFF.md` §C](HANDOFF.md); pre-submit checks in §D |

Nothing else is outstanding. **[`docs/HANDOFF.md`](HANDOFF.md) is the page to open next** — it has
a Vietnamese summary at the top, the YouTube listing text, the exact lines to edit in `README.md`,
this file and `docs/DEVPOST.md`, the Devpost form field by field, the three pre-submit verification
commands, what to do during the 23 Sep – 7 Oct judging window (keep the VM up; IPv4 ≈ $2.50/mo),
and an explicitly optional Grafana-track stretch.
