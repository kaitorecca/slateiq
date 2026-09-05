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
| — Clips + thumbnails in the hosted UI | takes play, posters render | ☐ **BROKEN** — `/clips/*` 404s and `/thumbs/*` returns the SPA HTML; the files are fine on GCS. `.gcloudignore` excludes `data/`. **P0 #1/#2** | JUDGE_REVIEW_2.md |
| — Grafana embedded in the product | Production Health shows the panels | ☐ **not wired** — screen shows "Set `VITE_GRAFANA_URL` …"; dashboard UID default is also wrong. **P1 #4/#5** | JUDGE_REVIEW_2.md |
| Public repo | GitHub, complete source + run instructions | ✅ public, description set, 29/29 relative links resolve, all 6 screenshots load, mermaid fence recognised | https://github.com/kaitorecca/slateiq |
| — README live URLs | hosted URL above the fold | ☐ **4× `<<PENDING>>` placeholders** still in the Live table + the curl; repo `homepage` field unset. **P0 #3** | README.md |
| — README eval numbers | match the linked artifact | ☐ README says 15/16 · 4.07/5; committed `agent/evals/last_run.md` says **16/16 · 4.88/5 · median 39.3 s**. **P1 #7** | agent/evals/last_run.md |
| License | OSI license file visible in About | ✅ **Apache-2.0** — GitHub sidebar + About screen | https://github.com/kaitorecca/slateiq/blob/main/LICENSE |
| Footage attribution | *Tears of Steel* CC BY 3.0 | ✅ in README and on the hosted About screen, with links to mango.blender.org and the licence | About screen |
| Video | ≤ 3 min, YouTube/Vimeo public, English | ☐ not shot / not published | docs/DEMO_SCRIPT.md → video/ |
| Text description | features, tech, data sources, learnings | ✅ drafted | docs/DEVPOST.md |
| Only Google AI | no non-Google model APIs in product | ✅ **verified** — `grep -rniE 'openai\|anthropic\|claude\|mistral\|cohere\|ollama\|llama' agent ingest db web/src` → 2 hits, both comments in `ingest/*.py` referencing CLAUDE.md. Re-run after the final commit. | — |
| Newly created | during 27 Jul–9 Sep 2026 | ✅ | git history |
| Team ≤ 4 | | ✅ | solo |

## Open risks

- **Cold start unmeasured.** Every probe in this pass was warm (`/api/health` TTFB 0.73 s). Revision
  has no `minScale`; the image is 565 MB. Measure once from idle, or keep the service warm during
  judging.
- **First DPR is ~200 s** on the hosted service — the pre-warmed cache is excluded from the image.
