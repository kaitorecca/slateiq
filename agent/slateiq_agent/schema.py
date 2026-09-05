"""Schema knowledge injected into every agent instruction.

`db/SCHEMA.md` is written by the data engineer and is the shared contract. We
load it at *runtime* (not import time is fine either way -- it is cheap and we
re-read when the mtime changes) so the agents always describe the live schema.
If the file has not landed yet we fall back to the embedded summary below,
which is derived from docs/PLAN.md and the agreed enum contract.
"""

from __future__ import annotations

import os
from pathlib import Path

from .config import DB, REPO_ROOT

SCHEMA_PATH = Path(
    os.environ.get("SLATEIQ_SCHEMA_MD", str(REPO_ROOT / "db" / "SCHEMA.md"))
)

FALLBACK_SCHEMA = f"""\
# SlateIQ ClickHouse schema (fallback summary -- db/SCHEMA.md not found)

Database: `{DB}`. Always fully qualify tables as `{DB}.<table>`.

## Tables
- `{DB}.production` -- one row per production. production_id, title, format,
  total_days, start_date, dp, director.
- `{DB}.scene` -- script breakdown. scene_id, production_id, scene_number,
  page_eighths (UInt/Int -- divide by 8.0 to get pages), int_ext ('INT'/'EXT'),
  day_night ('DAY'/'NIGHT'), location, characters (Array(String)), synopsis.
- `{DB}.shooting_day` -- call sheet / actuals. day_id, production_id,
  day_number, shoot_date, call_time, wrap_time, planned_scenes (Array(String)),
  unit, weather.
- `{DB}.take` -- one row per take. take_id, production_id, scene_id / scene_number,
  day_number, shot (e.g. '12A'), take_number, camera_roll, tc_in, tc_out,
  duration_s, status ('circled'|'ng'|'hold'|'wild'|'pending'), director_note,
  clip_uri.
- `{DB}.take_event` -- timestamped events inside a take. take_id, t_offset_s,
  kind ('dialogue'|'action'|'flag'|'slate'|'emotion'|'camera'), speaker,
  text, flag_type ('soft_focus'|'boom_in_shot'|'line_flub'|'overlap'|
  'continuity'|'frame_edge'|'audio_clip'|'crew_in_shot'), emotion, score.
- `{DB}.take_analysis` -- per-take Gemini summary/scores. take_id, summary,
  performance_score, technical_score, recommend (Bool), reasons.
- `{DB}.continuity_note` -- script-supervisor notes. note_id, scene_id/number,
  take_id, category, description, severity.
- `{DB}.frame_telemetry` -- per-second signals (the big table). take_id, t_s,
  focus_score, exposure, audio_peak_db, motion.

## Materialized views
- `{DB}.daily_progress` -- per shooting day rollup (takes, setups, pages, scenes).
- `{DB}.scene_progress` -- per scene rollup (takes, circled, pages).

## Domain rules
- Pages = page_eighths / 8.0. Report pages as e.g. "3 2/8" or 3.25.
- A "circled take" is `take.status = 'circled'` -- the take the editor should cut.
- Shooting ratio = total takes (or total footage duration) / printed (circled) takes.
- Setups = distinct `shot` values on a day.
"""

_cache: dict[str, tuple[float, str]] = {}


def load_schema_doc() -> str:
    """Return the schema doc, re-reading db/SCHEMA.md when it changes."""
    try:
        mtime = SCHEMA_PATH.stat().st_mtime
    except OSError:
        return FALLBACK_SCHEMA
    key = str(SCHEMA_PATH)
    cached = _cache.get(key)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_SCHEMA
    if not text.strip():
        return FALLBACK_SCHEMA
    _cache[key] = (mtime, text)
    return text


def schema_source() -> str:
    return str(SCHEMA_PATH) if SCHEMA_PATH.exists() else "embedded fallback"
