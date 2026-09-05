# `ingest/` — real dailies into ClickHouse

Turns real footage into the **day-12 dailies** slice of the SlateIQ database:
24 takes across 8 scenes, each with a Gemini-written analysis, timestamped
events, 25 Hz frame telemetry and cross-take continuity notes.

Everything else in the database (30 shooting days, millions of telemetry rows)
is synthetic and owned by `db/`. This directory owns exactly:

| | |
|---|---|
| production | `tos2026` |
| shooting day | `12` (2026-09-04) |
| scenes | `12`, `14A`, `27`, `33`, `41`, `56`, `78`, `102` |
| take ids | `TOS-D12-S<scene>-<setup>-<NN>-<camera>`, e.g. `TOS-D12-S27-A-02-A` |

Ranges and enums follow **`db/SCHEMA.md`**, not the raw model output:
`take_analysis.quality_score`, `frame_telemetry.focus_score` and `motion` are
**0..1**; `take_event.severity` and `continuity_note.severity` are **1..5**;
`continuity_note.category` is the eight-value house enum. `load.py` does the
conversion — Gemini is asked for 0..10 / 1..3, which it scores more reliably.

## Footage & attribution

`data/footage/tos.mp4` is **Tears of Steel** — (CC) Blender Foundation,
[mango.blender.org](https://mango.blender.org), licensed **CC-BY 3.0**. It is
used here as stand-in dailies footage; SlateIQ is not affiliated with the
Blender Foundation.

## Pipeline

```
data/footage/tos.mp4
   │  clips.py      ffmpeg scene detection (gt(scene,0.35)) → 18 original clips
   │                + 6 deliberately degraded "bad take" variants + thumbnails
   ▼
data/clips/<take_id>.mp4, data/thumbs/<take_id>.jpg
   │  analyze.py    Gemini File API upload → gemini-3.5-flash, JSON response_schema
   │                (transcript / actions / flags / emotions / camera / score)
   ▼
data/cache/<sha1 of clip>.json          ← committed, so re-runs cost nothing
   │  telemetry.py  ffmpeg raw pipes + numpy → 25 Hz focus / exposure / motion / audio dB
   │  continuity.py one text-only Gemini call per scene over the JSON analyses
   ▼
load.py → ClickHouse  take · take_event · take_analysis · frame_telemetry · continuity_note
```

### Run it

```bash
cd /path/to/block
./ingest/run_all.sh                # idempotent: cached clips + cached Gemini results
./ingest/run_all.sh --force-clips  # re-encode the clips
./ingest/run_all.sh --base-url https://storage.googleapis.com/<bucket>
```

`run_all.sh` sources `.venv` and `.env` itself. Individual steps:

```bash
python ingest/clips.py [--force]
python ingest/analyze.py [--dry-run] [--only TAKE_ID ...] [--model gemini-3.5-flash]
python ingest/telemetry.py [--only TAKE_ID ...]
python ingest/continuity.py [--offline]
python ingest/load.py --replace [--base-url URL] [--dry-run] [--offline-continuity]
```

## Files

| file | what it does |
|---|---|
| `config.py` | the **static take plan** — take ids, scene/shot/take numbers, camera, lens, ISO, timecode, director notes, source-footage in/out points, and which takes are degraded variants. Static on purpose: same ids and same cache keys on every run. |
| `clips.py` | cuts originals (720p h264 + `faststart`), renders the degraded variants, grabs thumbnails |
| `schema_models.py` | pydantic models used as Gemini `response_schema` |
| `gemini.py` | client, 429/5xx backoff with model fallback, token accounting, disk cache |
| `analyze.py` | one multimodal call per **original** clip |
| `telemetry.py` | vectorised 25 Hz telemetry from the clip itself (one row per frame) |
| `continuity.py` | one cheap text-only call per scene with ≥2 takes |
| `load.py` | builds and inserts every row; `--replace` for idempotency |
| `run_all.sh` | steps 1–5 |

## Cost control

* Only **original** clips are sent to Gemini — **263 s (~4.4 min) of video
  total**, against the project's 15-minute hard budget (`analyze.py` refuses to
  exceed 12). The full 18-clip pass costs ~53k tokens; continuity adds ~21k.
* Degraded variants **reuse their parent's analysis**. `load.py` then injects the
  corresponding flag event (`soft_focus` / `boom_in_shot` / `audio_clip` /
  `frame_edge`), drops `quality_score` by 0.25–0.35, sets `recommended = false`
  and the take's `status` to `ng`. This is honest: the defect really is in the
  file, and `telemetry.py` measures it independently from the clip without ever
  being told about it — `TOS-D12-S41-A-02-A` shows 5.5 s under the 0.55 focus
  threshold against 0.0 s for its parent, and `TOS-D12-S27-A-02-A` peaks at
  0.0 dBFS against −1.2 dBFS.
* Every Gemini result is cached at `data/cache/<sha1>.json` and **committed**, so
  a clean checkout replays the whole pipeline with zero API calls.
* Continuity is text-only: a few thousand tokens per scene, no video re-upload.

## Degradations

| variant | ffmpeg | flag emitted |
|---|---|---|
| soft focus | `gblur=sigma=14` over a window | `soft_focus` sev 5 |
| boom in shot | `drawbox` dipping in from frame top over 0.5 s | `boom_in_shot` sev 5 |
| audio clipping | `volume=10.0` (+20 dB) into hard clipping | `audio_clip` sev 3 |
| frame-edge drift | animated `crop` panning off the subject | `frame_edge` sev 3 |

## Media URIs

`clip_uri` / `thumb_uri` are relative by default — `clips/<take_id>.mp4`,
`thumbs/<take_id>.jpg` — and the web server mounts `data/` at that root. Deploy
rewrites them to GCS with `load.py --replace --base-url https://.../<bucket>`
(or the `SLATEIQ_MEDIA_BASE_URL` env var); no re-analysis is needed.

## Schema

The five tables written here follow the shared contract in `db/SCHEMA.md`.
`load.py` carries a `CREATE TABLE IF NOT EXISTS` copy of the DDL so it can run
before `db/schema.sql` has landed; `db/`'s `--reset` replaces those tables with
the canonical definitions and this loader is safe to re-run afterwards.

`take_daily_agg` / `take_scene_agg` are `AggregatingMergeTree` roll-ups fed by
materialized views on `INSERT INTO take`, and **a materialized view never sees a
`DELETE`**. So after replacing our slice, `load.py` rebuilds exactly the affected
roll-up keys (day 12, and the eight scenes) straight from `take`. Without that,
every re-run would double-count in `daily_progress` / `scene_progress`.
Confirm with `.venv/bin/python db/verify.py`.

ClickHouse is reached here with `clickhouse-connect` directly, which
`CLAUDE.md` permits for ingest/seed/admin scripts. The **agent** never does —
it goes through the official `mcp-clickhouse` server.
