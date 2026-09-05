#!/usr/bin/env python3
"""Step 5 — load the real-footage day-12 rows into ClickHouse.

Writes ``take``, ``take_event``, ``take_analysis``, ``frame_telemetry`` and
``continuity_note`` for production ``tos2026``, day 12, scenes 12/14A/27/33/41/
56/78/102.  Everything else in those tables is synthetic and owned by ``db/``.

Scales and enums follow ``db/SCHEMA.md``, not the raw Gemini output:
quality_score and focus_score/motion are 0..1, take_event.severity is 1..5,
continuity_note.category is the eight-value house enum.

Idempotent: ``--replace`` deletes exactly this slice (day 12 + our take ids)
before inserting, so the loader can run any number of times, before or after
``db/schema.sql --reset``.

Direct clickhouse-connect is used here on purpose — CLAUDE.md allows it for
ingest/seed/admin scripts; the *agent* only ever reaches ClickHouse through the
official mcp-clickhouse server.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta

import clickhouse_connect

from config import (
    DAY_NUMBER,
    PRODUCTION_ID,
    REAL_SCENES,
    SHOOT_DATE,
    TAKES,
    TAKES_BY_ID,
    Take,
    roll_for,
    sound_roll_for,
    FPS,
)

DB = os.environ.get("CLICKHOUSE_DB", "slateiq")

# --------------------------------------------------------------------------
# DDL — mirrors db/schema.sql. Only used if the data engineer's schema has not
# landed yet; their --reset will replace these tables with the canonical ones.
# --------------------------------------------------------------------------
DDL = [
    f"CREATE DATABASE IF NOT EXISTS {DB}",
    f"""CREATE TABLE IF NOT EXISTS {DB}.take (
        production_id String, take_id String, day_number UInt16, scene_number String,
        shot String, take_number UInt8, camera String, roll String, sound_roll String,
        clip_uri String, thumb_uri String, tc_in String, duration_s Float32,
        status String, director_note String, lens_mm UInt16, fps UInt8, iso UInt16,
        created_at DateTime
    ) ENGINE = MergeTree ORDER BY (production_id, take_id)""",
    f"""CREATE TABLE IF NOT EXISTS {DB}.take_event (
        production_id String, take_id String, event_id String, t_offset_s Float32,
        t_end_s Float32, kind String, speaker String, text String, flag_type String,
        severity UInt8, score Float32, meta String
    ) ENGINE = MergeTree ORDER BY (production_id, take_id)""",
    f"""CREATE TABLE IF NOT EXISTS {DB}.take_analysis (
        production_id String, take_id String, summary String, transcript String,
        quality_score Float32, recommended Bool, emotion_intensity Float32,
        performance_note String, model String, analyzed_at DateTime
    ) ENGINE = MergeTree ORDER BY (production_id, take_id)""",
    f"""CREATE TABLE IF NOT EXISTS {DB}.continuity_note (
        production_id String, scene_number String, take_id_a String, take_id_b String,
        category String, description String, severity UInt8, created_at DateTime
    ) ENGINE = MergeTree ORDER BY (production_id, scene_number)""",
    f"""CREATE TABLE IF NOT EXISTS {DB}.frame_telemetry (
        production_id String, take_id String, t_s Float32, focus_score Float32,
        exposure_ev Float32, motion Float32, audio_peak_db Float32, audio_rms_db Float32
    ) ENGINE = MergeTree ORDER BY (production_id, take_id)""",
]

TAKE_COLS = ["production_id", "take_id", "day_number", "scene_number", "shot",
             "take_number", "camera", "roll", "sound_roll", "clip_uri", "thumb_uri",
             "tc_in", "duration_s", "status", "director_note", "lens_mm", "fps",
             "iso", "created_at"]
EVENT_COLS = ["production_id", "take_id", "event_id", "t_offset_s", "t_end_s", "kind",
              "speaker", "text", "flag_type", "severity", "score", "meta"]
ANALYSIS_COLS = ["production_id", "take_id", "summary", "transcript", "quality_score",
                 "recommended", "emotion_intensity", "performance_note", "model",
                 "analyzed_at"]
CONT_COLS = ["production_id", "scene_number", "take_id_a", "take_id_b", "category",
             "description", "severity", "created_at"]
TELEM_COLS = ["production_id", "take_id", "t_s", "focus_score", "exposure_ev",
              "motion", "audio_peak_db", "audio_rms_db"]

# what an induced degradation looks like as a flag event (severity on the
# 1..5 house scale from db/SCHEMA.md)
DEGRADE_FLAG = {
    "soft_focus": (5, "Image goes soft through the middle of the take; the focus "
                      "puller never recovers the eyes."),
    "boom_in_shot": (5, "Boom microphone dips into the top of frame, left of centre."),
    "audio_clip": (3, "Production sound clips hard — the level slams into 0 dBFS and "
                      "distorts."),
    "frame_edge": (3, "Operator drifts right and the subject is cut by the frame edge."),
}
# Gemini scores severity 1..3; the database is 1..5
SEVERITY_MAP = {0: 0, 1: 2, 2: 3, 3: 5}
DEGRADE_EXTRA_NOTE = {
    "soft_focus": "Unusable for focus.",
    "boom_in_shot": "Unusable — boom in frame.",
    "audio_clip": "Sound department flagged clipping; picture is fine, needs ADR or a re-take.",
    "frame_edge": "Reframe drifts; only usable if we punch in.",
}


# The two AggregatingMergeTree roll-ups are fed by materialized views on
# INSERT INTO take, and a materialized view never sees a DELETE. So after
# replacing our slice we rebuild exactly the affected roll-up keys straight
# from `take`, which is the source of truth.
AGG_REPAIR = [
    ("take_daily_agg",
     "production_id = '{prod}' AND day_number = {day}",
     """SELECT production_id, day_number, count(), countIf(status='circled'),
               countIf(status='ng'), sum(toFloat64(duration_s)),
               uniqState(concat(scene_number, '/', shot))
        FROM {db}.take WHERE production_id='{prod}' AND day_number={day}
        GROUP BY production_id, day_number"""),
    ("take_scene_agg",
     "production_id = '{prod}' AND scene_number IN ({scenes})",
     """SELECT production_id, scene_number, count(), countIf(status='circled'),
               countIf(status='ng'), sum(toFloat64(duration_s)), uniqState(shot),
               min(day_number), max(day_number)
        FROM {db}.take WHERE production_id='{prod}' AND scene_number IN ({scenes})
        GROUP BY production_id, scene_number"""),
]


def repair_aggregates(cl) -> None:
    scenes = ", ".join(f"'{s}'" for s in REAL_SCENES)
    fmt = {"db": DB, "prod": PRODUCTION_ID, "day": DAY_NUMBER, "scenes": scenes}
    for table, where, select in AGG_REPAIR:
        if not cl.command(f"EXISTS TABLE {DB}.{table}"):
            continue
        cl.command(f"DELETE FROM {DB}.{table} WHERE " + where.format(**fmt),
                   settings={"mutations_sync": 2})
        cl.command(f"INSERT INTO {DB}.{table} " + select.format(**fmt))
    print("  rebuilt take_daily_agg / take_scene_agg for the affected keys")


def tc_to_dt(tc: str) -> datetime:
    h, m, s = (int(x) for x in tc.split(":")[:3])
    return datetime.fromisoformat(SHOOT_DATE) + timedelta(hours=h, minutes=m, seconds=s)


def uri(rel: str, base_url: str | None) -> str:
    if not base_url:
        return rel
    return base_url.rstrip("/") + "/" + rel


# --------------------------------------------------------------------------
# row builders
# --------------------------------------------------------------------------
def build_rows(base_url: str | None, live_continuity: bool):
    from analyze import load_cached
    from clips import probe_duration
    from continuity import all_notes
    from telemetry import telemetry_rows

    takes, events, analyses, telemetry = [], [], [], []
    missing: list[str] = []
    now = datetime.now().replace(microsecond=0)

    for t in TAKES:
        if not t.clip_path.exists():
            missing.append(t.take_id)
            continue
        duration = probe_duration(t.clip_path)
        takes.append([
            PRODUCTION_ID, t.take_id, DAY_NUMBER, t.scene_number, t.shot,
            t.take_number, t.camera, roll_for(t), sound_roll_for(t),
            uri(t.clip_rel, base_url), uri(t.thumb_rel, base_url), t.tc_in,
            round(duration, 3), t.status, t.director_note, t.lens_mm, FPS, t.iso,
            tc_to_dt(t.tc_in),
        ])

        # telemetry always comes from the take's OWN clip (variants included)
        for r in telemetry_rows(t, duration):
            telemetry.append([PRODUCTION_ID, t.take_id, *r])

        src = TAKES_BY_ID[t.parent] if t.is_variant else t
        cached = load_cached(src)
        if cached is None:
            missing.append(t.take_id)
            continue
        a = cached["analysis"]
        events.extend(events_for(t, a, duration))
        analyses.append(analysis_row(t, a, cached))

    cont = []
    for scene, n in all_notes(live=live_continuity):
        cont.append([PRODUCTION_ID, scene, n["take_id_a"], n["take_id_b"],
                     n["category"], n["description"],
                     SEVERITY_MAP.get(int(n["severity"]), 3), now])

    return takes, events, analyses, cont, telemetry, missing


def events_for(t: Take, a: dict, duration: float) -> list[list]:
    rows: list[list] = []
    n = 0

    def add(t_off, t_end, kind, speaker, text, flag_type, severity, score, meta):
        nonlocal n
        n += 1
        rows.append([
            PRODUCTION_ID, t.take_id, f"{t.take_id}_e{n:03d}",
            round(min(float(t_off), duration), 3),
            round(min(float(t_end), duration), 3),
            kind, speaker, text, flag_type, int(severity), float(score),
            json.dumps(meta, separators=(",", ":")),
        ])

    slate_text = f"Scene {t.scene_number} {t.shot} take {t.take_number} camera {t.camera}"
    add(0.0, min(2.0, duration), "slate", "", slate_text, "", 0, 0.0,
        {"marker": "head", "read": a.get("slate", "")})
    for seg in a.get("transcript", []):
        add(seg["start"], seg["end"], "dialogue", seg["speaker"], seg["text"], "", 0, 0.0, {})
    for beat in a.get("actions", []):
        add(beat["start"], beat["end"], "action", "", beat["text"], "", 0, 0.0, {})
    for e in a.get("emotions", []):
        add(e["start"], e["end"], "emotion", "", e["label"], "", 0,
            float(e["intensity"]), {"label": e["label"]})
    for c in a.get("camera", []):
        add(c["start"], c["end"], "camera", "", c["text"], "", 0, 0.0, {})
    for f in a.get("flags", []):
        add(f["start"], f["end"], "flag", "", f["evidence"], f["type"],
            SEVERITY_MAP.get(int(f["severity"]), 3), 0.0, {"source": "gemini"})

    # the induced defect on a degraded variant
    if t.is_variant:
        sev, evidence = DEGRADE_FLAG[t.degrade]
        s, e = t.defect_window
        add(s, e, "flag", "", evidence, t.degrade, sev, 0.0,
            {"source": "induced", "parent_take_id": t.parent})
    return rows


def analysis_row(t: Take, a: dict, cached: dict) -> list:
    transcript = " ".join(
        f"{s['speaker']}: {s['text']}" for s in a.get("transcript", [])
    ).strip()
    emo = [float(e["intensity"]) for e in a.get("emotions", [])]
    emotion_intensity = round(min(1.0, max(emo)), 3) if emo else 0.0
    score = float(a["quality_score"]) / 10.0   # Gemini scores 0..10, the db is 0..1
    summary = a["summary"]
    note = a["performance_note"]
    recommended = bool(a["recommended"])

    if t.is_variant:
        sev, evidence = DEGRADE_FLAG[t.degrade]
        score = round(max(0.05, score - (0.35 if sev >= 5 else 0.25)), 3)
        recommended = False
        summary = f"{summary} Technical problem on this take: {evidence}"
        note = f"{note} {DEGRADE_EXTRA_NOTE[t.degrade]}"

    return [
        PRODUCTION_ID, t.take_id, summary, transcript, score, recommended,
        emotion_intensity, note, cached["model"],
        datetime.strptime(cached["analyzed_at"], "%Y-%m-%d %H:%M:%S"),
    ]


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="load real day-12 dailies into ClickHouse")
    ap.add_argument("--replace", action="store_true",
                    help="delete this slice (day 12, real scenes) before inserting")
    ap.add_argument("--base-url", default=os.environ.get("SLATEIQ_MEDIA_BASE_URL"),
                    help="prefix clip_uri/thumb_uri, e.g. https://storage.googleapis.com/bucket")
    ap.add_argument("--offline-continuity", action="store_true",
                    help="use only cached continuity results")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("building rows ...")
    takes, events, analyses, cont, telem, missing = build_rows(
        args.base_url, live_continuity=not args.offline_continuity)
    print(f"  take={len(takes)} take_event={len(events)} take_analysis={len(analyses)} "
          f"continuity_note={len(cont)} frame_telemetry={len(telem)}")
    if missing:
        print(f"  !! no clip/analysis for: {sorted(set(missing))}")
    if args.dry_run:
        return 0

    cl = clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", "clickhouse"),
    )
    for stmt in DDL:
        cl.command(stmt)

    if args.replace:
        ids = "', '".join(t[1] for t in takes)
        scenes = "', '".join(REAL_SCENES)
        settings = {"mutations_sync": 2}
        cl.command(f"DELETE FROM {DB}.take WHERE production_id='{PRODUCTION_ID}' "
                   f"AND day_number={DAY_NUMBER} AND scene_number IN ('{scenes}')",
                   settings=settings)
        for tbl in ("take_event", "take_analysis", "frame_telemetry"):
            cl.command(f"DELETE FROM {DB}.{tbl} WHERE production_id='{PRODUCTION_ID}' "
                       f"AND take_id IN ('{ids}')", settings=settings)
        cl.command(f"DELETE FROM {DB}.continuity_note WHERE production_id='{PRODUCTION_ID}' "
                   f"AND (take_id_a IN ('{ids}') OR take_id_b IN ('{ids}'))",
                   settings=settings)
        print("  replaced: deleted existing day-12 real-footage rows")

    cl.insert(f"{DB}.take", takes, column_names=TAKE_COLS)
    cl.insert(f"{DB}.take_event", events, column_names=EVENT_COLS)
    cl.insert(f"{DB}.take_analysis", analyses, column_names=ANALYSIS_COLS)
    if cont:
        cl.insert(f"{DB}.continuity_note", cont, column_names=CONT_COLS)
    cl.insert(f"{DB}.frame_telemetry", telem, column_names=TELEM_COLS)
    print("inserted.")
    repair_aggregates(cl)

    q = cl.query(f"""SELECT scene_number, count(), countIf(status='circled'), countIf(status='ng')
                     FROM {DB}.take WHERE production_id='{PRODUCTION_ID}'
                     AND day_number={DAY_NUMBER} AND scene_number IN
                     ('{"', '".join(REAL_SCENES)}') GROUP BY scene_number ORDER BY scene_number""")
    for row in q.result_rows:
        print(f"  scene {row[0]:>4}: {row[1]} takes ({row[2]} circled, {row[3]} ng)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
