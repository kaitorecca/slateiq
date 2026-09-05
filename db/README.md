# db/ — SlateIQ ClickHouse data model + synthetic production

| File | What |
|---|---|
| `schema.sql` | DDL for database `slateiq`: 8 base tables, 2 aggregating MVs, 3 dashboard views |
| `generate_synthetic.py` | Deterministic (seed 20260905) generator for a fictional 30-day *Tears of Steel* shoot |
| `SCHEMA.md` | **Agent-facing contract** — injected into the ADK agent prompt. Tables, enums, joins, 15 golden Q→SQL, gotchas. Keep it under 6 KB |
| `verify.py` | Row counts, MV/invariant checks, runs every golden query from `SCHEMA.md`. Non-zero exit on failure |

## Run

```bash
set -a; source .env; set +a
uv pip install --python .venv/bin/python numpy pyarrow clickhouse-connect
.venv/bin/python db/generate_synthetic.py --reset     # ~4s, drops & rebuilds slateiq
.venv/bin/python db/verify.py                         # 43 checks
```

Flags: `--reset` (drop + recreate), `--telemetry-hz 25`, `--seed 20260905`.
Connects via `CLICKHOUSE_HOST/PORT/USER/PASSWORD/SECURE` (defaults localhost:8123 / default / clickhouse).

## The world

*Tears of Steel* (Blender Foundation, CC-BY 3.0), fictionalised as a 30-shooting-day feature in
Amsterdam, dir. Ian Hubert. **Day 12 = 2026-09-04 = today.**

- Days 1–12 shot (takes, timed events, Gemini-style analysis, frame telemetry).
- Days 13–30 planned only — no takes, so schedule-risk questions have something to forecast.
- Days 8 and 11 lost setups to rain: overtime + planned scenes with zero takes.
- Scenes `12, 14A, 27, 33, 41, 56, 78, 102` are on day 12 and are **left empty on purpose** —
  `ingest/` loads real clips from `data/footage/tos.mp4` into those scene numbers.

Approx. volumes: 120 scenes · 30 days · ~2.5k takes · ~26k take events · ~2.5k analyses ·
60 continuity notes · **3.0M+ frame_telemetry rows** (25 Hz per take).

## Notes for other owners

- Ingest: insert takes with `scene_number` from the reserved list and `day_number=12`; the MVs
  update automatically. Tables are plain MergeTree — **delete before re-inserting** a take_id.
- Agents: read via `mcp-clickhouse` only. `SCHEMA.md` is the prompt contract; if a column changes,
  change it there too and re-run `verify.py`.
