# Tracking
| Time (AEST) | Who | Item | Status |
|---|---|---|---|
| 13:36 | orchestrator | env ready: ADK 2.8 + mcp-clickhouse 0.6 (HTTP :8765) + CH docker + Gemini key + gcloud | done |
| 13:52 | orchestrator | tick: CH seeded (take 2479, take_event 26.5k, frame_telemetry 3.07M); 5 build agents running; local ports: API→8811 (8080/3000 taken by other apps) | in progress |
| 14:12 | data eng | db/: slateiq schema + 3.07M-row synthetic 30-day shoot, SCHEMA.md contract, verify.py 43/43 green | done |
| 13:55 | data eng | db/ done: schema + 3.07M-row synthetic shoot, verify 43/43, SCHEMA.md contract (production_id=tos2026, day12=2026-09-04) | done |
| 14:20 | frontend | web/ done: 4-screen React SPA (Ask+live MCP agent trace, Takes browser+player drawer, Production Health+DPR/TTS, About+arch SVG), mock API server, dist committed, build/typecheck green, README with API contract | done |
| 14:10 | frontend | web/ done: 4 screens, agent trace panel, dist committed (dev :5188, API :8811) | done |
| 14:32 | ingest eng | ingest/ done: 24 real day-12 takes from Tears of Steel (18 Gemini-analysed originals + 6 degraded NG variants), 232 events, 24 analyses, 8,599 telemetry rows @25Hz, 6 continuity notes → ClickHouse (tos2026, scenes 12/14A/27/33/41/56/78/102). 263s of video to Gemini (~53k tok) + 8 text-only continuity calls (~21k tok), all cached in data/cache and committed. run_all.sh idempotent, db/verify.py 43/43 green. NOTE: load.py rebuilds take_daily_agg/take_scene_agg for its keys after --replace, because the MVs feeding them never see a DELETE — anyone else deleting from `take` must do the same. .gitignore now excludes data/ except data/cache. | done |
| 14:15 | ingest | ingest/ done: 18 real clips + 6 NG variants, Gemini 3.5 flash analysis cached, telemetry 25Hz, continuity notes; verify 43/43 | done |
| 14:02 | orchestrator | tick: agent+deploy still building; launched judge-style pitch review agent (docs only) | in progress |
| 14:35 | judge/pitch | docs/JUDGE_REVIEW_1.md: scored 15/20 today (tech 4, design 4, impact 3, idea 4); top-10 fixes; rewrote DEVPOST.md + DEMO_SCRIPT.md with real DB numbers. BLOCKERS: no root README, no Cloud Run URL, hosted MCP /health = "ClickHouse connection failed", evals/last_run.md missing (README links to it). BUG: "shooting ratio" is defined as takes/circled in SCHEMA.md + prompts.py + DPR template — that is *print ratio*; real shooting ratio is material shot vs final cut. Also say "Google Cloud Agent Builder (ADK)" at least once — the rule names Agent Builder. | done |
