# Submission checklist — Agentic Cinema (ClickHouse track)
Deadline: 9 Sep 2026 14:00 PDT = 10 Sep 07:00 AEST.

Status verified remotely on **5 Sep 2026 06:00–06:20 UTC** — hosted URLs only, no local stack.
Evidence and repro for every line: [`JUDGE_REVIEW_2.md`](JUDGE_REVIEW_2.md).

| Item | Requirement | Status | Where |
|---|---|---|---|
| Partner track | ClickHouse — official `mcp-clickhouse` used at runtime | ✅ **verified live** — `/api/health` returns `mcp:"up"`; 4 hosted questions each streamed `run_query` · `via mcp-clickhouse` · SQL · real row counts; endpoint returns 401 without bearer | https://slateiq-957930801789.us-central1.run.app/api/health · https://35.239.36.85.sslip.io/health |
| Google Cloud | Gemini (google-genai/ADK), Cloud Run, GCS, Secret Manager | ✅ **verified live** — `gemini-3.5-flash` + `gemini-2.5-flash-preview-tts` reported by `/api/health`; two Cloud Run services; public GCS bucket (48 objects, `access-control-allow-origin: *`); 2 Secret Manager secrets | deploy/OUTPUT.md |
| Hosted URL | public, testable by judges | ✅ **200, no auth** — 4 questions answered end to end (20 s / 28 s / 45 s / 2.4 s refusal); 0 console errors; clean at 390 px | https://slateiq-957930801789.us-central1.run.app |
| — Grafana dashboard | anonymous, embeddable, data in every panel | ✅ **8/8 panels return data, 0 "No data"**, anonymous Viewer, cross-origin iframe loads | https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health |
| — Clips + thumbnails in the hosted UI | takes play, posters render | ✅ **fixed & verified 5 Sep 16:37 UTC** — the server rewrites relative `clip_uri`/`thumb_uri` to `$CLIPS_BASE_URL` at response time, so `/api/takes?scene=27` returns `https://storage.googleapis.com/…` (clip `200 video/mp4`, thumb `200 image/jpeg`). Hosted Takes: **24/24 posters load, a clip plays inline** (1280×534, `readyState 4`), 0 console errors. `data/thumbs` is also baked into the image; `/thumbs/*` now 404s honestly instead of returning the SPA HTML | docs/img/takes.png |
| — Grafana embedded in the product | Production Health shows the panels | ✅ **fixed & verified** — new `GET /api/config` hands the static build the server env at boot, so the screen embeds four `d-solo` iframes on the real UID `slateiq-prod-health` with the real panel ids/titles (2 Schedule position · 1 Pages planned vs shot · 3 Print ratio by scene · 8 Scenes at risk), pinned to the shoot's time range. Grafana's own title bar is clipped so the title is not printed twice | docs/img/health.png |
| Public repo | GitHub, complete source + run instructions | ✅ public, description set, 29/29 relative links resolve, all 6 screenshots load, mermaid fence recognised | https://github.com/kaitorecca/slateiq |
| — README live URLs | hosted URL above the fold | ✅ **fixed** — Live table and the reproduce-it curl carry the real URLs; repo `homepage` set to the Cloud Run URL and 6 topics added (`gemini`, `google-adk`, `clickhouse`, `mcp`, `hackathon`, `film-production`) | README.md |
| — README eval numbers | match the linked artifact | ✅ **fixed** — README now states the committed 28-question run: **28/28 reached `run_query`, 27/28 routed, judge mean 4.82/5, median latency 27.3 s**. No partial run was committed | agent/evals/last_run.md |
| License | OSI license file visible in About | ✅ **Apache-2.0** — GitHub sidebar + About screen | https://github.com/kaitorecca/slateiq/blob/main/LICENSE |
| Footage attribution | *Tears of Steel* CC BY 3.0 | ✅ in README and on the hosted About screen, with links to mango.blender.org and the licence | About screen |
| Video | ≤ 3 min, YouTube/Vimeo public, English | ☐ not shot / not published | docs/DEMO_SCRIPT.md → video/ |
| Text description | features, tech, data sources, learnings | ✅ drafted | docs/DEVPOST.md |
| Only Google AI | no non-Google model APIs in product | ✅ **verified** — `grep -rniE 'openai\|anthropic\|claude\|mistral\|cohere\|ollama\|llama' agent ingest db web/src` → 2 hits, both comments in `ingest/*.py` referencing CLAUDE.md. Re-run after the final commit. | — |
| Newly created | during 27 Jul–9 Sep 2026 | ✅ | git history |
| Team ≤ 4 | | ✅ | solo |

## Open risks

- **Cold start measured: ~16 s.** Cloud Run logs, instance start → `Application startup complete`,
  is 15.7 s; it is the ADK import, not the database. Warm requests are ~0.6 s. `min-instances`
  stays 0 because an idle instance costs money and the free tier is the whole point; the README
  states the real number rather than the old "3–5 s" guess.
- **First DPR is now 0.7 s** — `data/cache/reports` and `data/cache/tts` ship in the image, so
  day 12's report and its read-aloud are served from the pre-warmed cache (was ~200 s).
