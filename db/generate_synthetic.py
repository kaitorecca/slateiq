#!/usr/bin/env python3
"""SlateIQ synthetic dailies generator.

Deterministic (seeded) generator for a fictional 30-shooting-day feature film
production of "Tears of Steel" (Blender Foundation, CC-BY 3.0) relocated to a
30-day Amsterdam shoot in Aug/Sep 2026.

  * days 1..12 are SHOT (takes, events, analysis, frame telemetry)
  * day 12 is "today" — the day the dailies land
  * days 13..30 are PLANNED only (no takes) so schedule-risk questions forecast
  * 8 scene numbers on day 12 are RESERVED for the real-clip ingest pipeline:
        12, 14A, 27, 33, 41, 56, 78, 102
    scene rows exist for them, but this script writes NO takes there.

Usage:
    python db/generate_synthetic.py --reset
    python db/generate_synthetic.py --reset --telemetry-hz 25
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import random
import sys
import time

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import clickhouse_connect

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20260905
PROD = "tos2026"
TITLE = "Tears of Steel"
DIRECTOR = "Ian Hubert"
DP = "Sander Houtman"
PLANNED_DAYS = 30
TODAY_DAY = 12
DAY12_DATE = dt.date(2026, 9, 4)  # day 12 == most recent shooting day
RESERVED = ["12", "14A", "27", "33", "41", "56", "78", "102"]
FPS = 25

# --------------------------------------------------------------- content banks
CHARACTERS = ["Thom", "Celia", "Barley", "Dr. Willem", "Frank", "Captain",
              "Sentry Robot", "Medic Drone", "Bartender", "Cadet Iris"]

LOCATIONS = [
    "Stage 1 - Vondel Studios, Amsterdam",
    "Stage 2 - Vondel Studios, Amsterdam",
    "Sloterdijk Warehouse, Amsterdam",
    "Amstel Bridge, Amsterdam",
    "Nemo Rooftop, Amsterdam",
    "Zuiderkerk Alley, Amsterdam",
    "Dam Square (permit), Amsterdam",
    "Westergasfabriek Yard, Amsterdam",
    "IJ Waterfront Quay, Amsterdam",
    "Oosterdok Lab Set - Stage 3",
]

SET_NAMES = [
    ("INT", "LAB"), ("INT", "SAFEHOUSE"), ("INT", "BAR"), ("INT", "CORRIDOR"),
    ("INT", "CONTROL ROOM"), ("INT", "WORKSHOP"), ("INT", "MED BAY"),
    ("EXT", "BRIDGE"), ("EXT", "ROOFTOP"), ("EXT", "ALLEY"), ("EXT", "QUAY"),
    ("EXT", "CITY SQUARE"), ("EXT", "RUINED STREET"), ("EXT", "CANAL BANK"),
]

SYNOPSIS_BITS = [
    "{a} confronts {b} about the machine and refuses to back down.",
    "{a} works the console while sentries close in on the perimeter.",
    "{a} and {b} argue over the timeline; the argument turns personal.",
    "Flashback: {a} remembers the day everything went wrong.",
    "{a} rigs the emitter under fire while {b} covers the stairwell.",
    "{a} walks the quay alone; the city burns on the horizon.",
    "{b} briefs the team; the plan is thin and everyone knows it.",
    "A sentry robot corners {a}; {b} arrives one beat too late.",
    "{a} tries an apology forty years overdue.",
    "The team loses contact with {b}; {a} makes the call to go back.",
]

LINE_BANK = {
    "Thom": [
        "I can't do this again.", "It was never about the machine.",
        "Give me thirty seconds and stay off the comms.",
        "You were right. I hate that you were right.",
        "I'm not leaving her down there.", "Then we do it the hard way.",
    ],
    "Celia": [
        "Forty years, Thom. Forty years I waited for you to say that.",
        "You don't get to apologise now.",
        "The emitter won't hold past the third pulse.",
        "I built it. I know exactly what it costs.",
        "Say it again. Say it like you mean it.",
        "Forty years and you still can't look at me.",
    ],
    "Barley": [
        "Perimeter's hot, two contacts north.", "We're out of time and out of ammo.",
        "Somebody tell me that was the plan.", "I've got eyes on the stairwell.",
        "Move, move, move!",
    ],
    "Dr. Willem": [
        "The field is unstable, you understand what that means.",
        "One more pulse and we lose the whole block.",
        "I warned the committee. Nobody listened.",
        "Numbers don't negotiate, Captain.",
    ],
    "Frank": [
        "You bring that thing in here, you bring the war with it.",
        "Drink's on the house. The advice isn't.",
        "I knew your father. He'd have run.",
    ],
    "Captain": [
        "Hold the line until the emitter is clear.",
        "This is not a rescue. This is a retrieval.",
        "You have four minutes. Use three.",
    ],
    "Sentry Robot": ["TARGET ACQUIRED.", "COMPLY.", "PERIMETER BREACH, SECTOR NINE."],
    "Medic Drone": ["VITALS CRITICAL.", "HOLD STILL."],
    "Bartender": ["We're closing.", "Not in here you don't."],
    "Cadet Iris": ["Sir, the readings just doubled.", "I can reroute through the west grid."],
}

ACTIONS = [
    "Thom crosses to the console.", "Celia turns away from camera.",
    "Sentry steps into frame left.", "Barley reloads and moves right.",
    "Emitter flares; practical light hits the ceiling.",
    "Hero prop handed off across the table.", "Rain hits the glass.",
    "Camera cranes down to eyeline.", "Stunt double takeover for the fall.",
]

DIRECTOR_NOTES = [
    "print it", "one more for safety", "too fast, let it breathe",
    "great, but eyeline drifted", "hold the pause before the last line",
    "less shouty", "boom dipped, go again", "focus soft on the turn",
    "loved the stillness", "reset props, hero glass moved",
    "sound reported a plane", "camera bumped the dolly", "keep for the cutaway",
    "circle this one", "she found it — that's the take",
    "second unit will pick up the insert",
]

PERF_NOTES = [
    "Grounded, quiet, holds the silence.", "Rushed the button line.",
    "Best emotional landing so far.", "Technically clean, performance flat.",
    "Big swing — usable but broad.", "Nice overlap with the off-camera cue.",
    "Eyes stay in it right to the cut.", "Slight anticipation before the door.",
]

FLAGS = [  # (flag_type, probability per take, severity range)
    ("soft_focus", 0.080, (2, 4)),
    ("line_flub", 0.050, (1, 3)),
    ("boom_in_shot", 0.030, (2, 5)),
    ("overlap", 0.030, (1, 3)),
    ("frame_edge", 0.025, (1, 3)),
    ("continuity", 0.020, (2, 4)),
    ("audio_clip", 0.020, (2, 4)),
    ("crew_in_shot", 0.010, (3, 5)),
]

CONT_CATEGORIES = ["wardrobe", "props", "hair_makeup", "screen_direction",
                   "lighting", "action_match", "dialogue", "set_dressing"]
CONT_DESCR = {
    "wardrobe": "Jacket zipped in {a} but open in {b} at the same beat.",
    "props": "Hero glass is half full in {a}, nearly empty in {b}.",
    "hair_makeup": "Blood on left temple in {a}, right temple in {b}.",
    "screen_direction": "Exit is camera-right in {a}, camera-left in {b}.",
    "lighting": "Practical is on in {a} and off in {b}; grade cannot match.",
    "action_match": "Hand-off happens on the line in {a}, after it in {b}.",
    "dialogue": "Line changed from scripted wording in {b} vs {a}.",
    "set_dressing": "Chair moved 40cm between {a} and {b}.",
}

WEATHER_OK = ["Clear, 21C, light NW wind", "Overcast, 19C, dry",
              "High cloud, 22C", "Sunny spells, 20C", "Still and mild, 18C"]
WEATHER_BAD = ["Heavy rain from 11:00, 15C, gusting 40km/h",
               "Persistent drizzle, 14C, low cloud"]


# ----------------------------------------------------------------- helpers
def shooting_dates(day12: dt.date, n_days: int) -> dict[int, dt.date]:
    """Mon-Fri shooting days, day 12 anchored on `day12`."""
    dates: dict[int, dt.date] = {}
    d = day12
    for k in range(TODAY_DAY, 0, -1):
        dates[k] = d
        d -= dt.timedelta(days=1)
        while d.weekday() >= 5:
            d -= dt.timedelta(days=1)
    d = day12
    for k in range(TODAY_DAY + 1, n_days + 1):
        d += dt.timedelta(days=1)
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        dates[k] = d
    return dates


def tc(seconds: float) -> str:
    s = int(seconds)
    f = int(round((seconds - s) * FPS)) % FPS
    return f"{s // 3600 % 24:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{f:02d}"


def scene_sort_key(sn: str):
    num = int("".join(c for c in sn if c.isdigit()))
    suf = "".join(c for c in sn if c.isalpha())
    return (num, suf)


# ------------------------------------------------------------------ builders
def build_scenes(rng: random.Random):
    numbers = [str(i) for i in range(1, 113)]
    numbers += ["14A", "27A", "41A", "56A", "78A", "88A", "102A", "109A"]
    numbers.sort(key=scene_sort_key)
    assert len(numbers) == 120
    for r in RESERVED:
        assert r in numbers, r

    scenes = []
    for i, sn in enumerate(numbers):
        int_ext, setname = rng.choice(SET_NAMES)
        dn = rng.choices(["DAY", "NIGHT", "DUSK", "DAWN"], [0.5, 0.35, 0.1, 0.05])[0]
        cast = rng.sample(CHARACTERS[:6], k=rng.choice([1, 2, 2, 2, 3, 3, 4]))
        if rng.random() < 0.18:
            cast.append(rng.choice(CHARACTERS[6:]))
        a = cast[0]
        b = cast[1] if len(cast) > 1 else rng.choice(CHARACTERS)
        scenes.append(dict(
            production_id=PROD,
            scene_number=sn,
            slug=f"{int_ext}. {setname} - {dn}",
            int_ext=int_ext,
            day_night=dn,
            page_eighths=int(rng.choices([2, 3, 4, 5, 6, 8, 10, 12, 16, 20],
                                         [6, 10, 14, 14, 14, 14, 10, 8, 6, 4])[0]),
            synopsis=rng.choice(SYNOPSIS_BITS).format(a=a, b=b),
            characters=cast,
            location=LOCATIONS[i % len(LOCATIONS)],
            script_day=1 + (i * 7) % 24,
            est_setups=rng.choices([3, 4, 5, 6, 7, 8, 9], [8, 16, 20, 20, 16, 12, 8])[0],
        ))
    return scenes


def build_schedule(scenes, rng: random.Random):
    """Assign every scene to a shooting day. Day 12 holds the 8 reserved scenes."""
    others = [s["scene_number"] for s in scenes if s["scene_number"] not in RESERVED]
    rng.shuffle(others)
    per_day = {d: [] for d in range(1, PLANNED_DAYS + 1)}
    per_day[TODAY_DAY] = list(RESERVED)

    # days 1..11 get 4-5 scenes, day 12 gets 3 extra, 13..30 get the rest
    quota = {}
    for d in range(1, PLANNED_DAYS + 1):
        if d == TODAY_DAY:
            quota[d] = 3
        elif d <= 11:
            quota[d] = 4
        else:
            quota[d] = 4
    idx = 0
    for d in range(1, PLANNED_DAYS + 1):
        take_n = min(quota[d], len(others) - idx)
        per_day[d] += others[idx:idx + take_n]
        idx += take_n
    # leftovers spread over the back half
    d = 13
    while idx < len(others):
        per_day[d].append(others[idx]); idx += 1
        d = 13 + (d - 12) % (PLANNED_DAYS - 12)
    for d in per_day:
        per_day[d].sort(key=scene_sort_key)
    return per_day


def build_days(per_day, scene_by_num, dates, rng: random.Random):
    rows = []
    for d in range(1, PLANNED_DAYS + 1):
        date = dates[d]
        night_heavy = sum(1 for sn in per_day[d]
                          if scene_by_num[sn]["day_night"] == "NIGHT") >= 2
        call_h = 15 if night_heavy else (7 if d % 5 else 6)
        call = dt.datetime.combine(date, dt.time(call_h, 0))
        planned_wrap = call + dt.timedelta(hours=12)
        loc = scene_by_num[per_day[d][0]]["location"] if per_day[d] else LOCATIONS[0]
        behind = d in (8, 11)
        weather = rng.choice(WEATHER_BAD if behind else WEATHER_OK)
        if d > TODAY_DAY:
            actual = None
            notes = "Scheduled. Not yet shot."
        elif behind:
            actual = planned_wrap + dt.timedelta(minutes=rng.randint(95, 165))
            notes = ("Weather hold — lost setups to rain; scenes carried to the "
                     "next available day. Company moved late.")
        else:
            over = rng.choices([-25, -10, 0, 15, 35, 60, 85],
                               [1, 2, 3, 4, 3, 2, 1])[0]
            actual = planned_wrap + dt.timedelta(minutes=over)
            notes = ("Wrapped on schedule." if over <= 0 else
                     f"Overtime {over} min — extra coverage on the last setup.")
        rows.append(dict(
            production_id=PROD, day_number=d, shoot_date=date,
            unit="second" if d in (6, 17) else "main",
            call_time=call, planned_wrap=planned_wrap, actual_wrap=actual,
            planned_scenes=per_day[d], location=loc, weather=weather, notes=notes))
    return rows


def build_takes(per_day, scene_by_num, dates, rng: random.Random, nprng):
    takes, events, analyses = [], [], []
    ev_seq = 0
    # Days 8 and 11 lost time to weather: the last planned scenes were never shot.
    slipped = {8: 2, 11: 2}
    for d in range(1, TODAY_DAY + 1):
        day_scenes = [sn for sn in per_day[d] if sn not in RESERVED]
        if d in slipped:
            day_scenes = day_scenes[:-slipped[d]]
        clock = 8.0 * 3600  # timecode hour-of-day start
        for sn in day_scenes:
            sc = scene_by_num[sn]
            behind = d in (8, 11)
            n_setups = max(2, sc["est_setups"] - (2 if behind else 0))
            for si in range(n_setups):
                shot = chr(ord("A") + si)
                cams = ["A"]
                if si == 0 or rng.random() < 0.68:
                    cams.append("B")
                if rng.random() < 0.16:
                    cams.append("C")
                n_takes = rng.choices([2, 3, 4, 5, 6, 7, 8, 11],
                                      [8, 16, 20, 18, 14, 10, 8, 6])[0]
                circled_take = rng.randint(max(1, n_takes - 2), n_takes)
                second_circle = n_takes - 3 if (rng.random() < 0.18 and n_takes > 4) else -1
                for tn in range(1, n_takes + 1):
                    dur = float(np.clip(nprng.lognormal(3.80, 0.42), 9, 190))
                    for cam in cams:
                        if tn in (circled_take, second_circle):
                            status = "circled"
                        elif rng.random() < 0.30:
                            status = "ng"
                        elif rng.random() < 0.12:
                            status = "hold"
                        else:
                            status = "pending" if (d == TODAY_DAY and rng.random() < 0.25) else "hold"
                        if rng.random() < 0.02:
                            status = "wild"
                        take_id = f"TOS-D{d:02d}-S{sn}-{shot}-{tn:02d}-{cam}"
                        created = (dt.datetime.combine(dates[d], dt.time(0, 0))
                                   + dt.timedelta(seconds=clock))
                        tk = dict(
                            production_id=PROD, take_id=take_id, day_number=d,
                            scene_number=sn, shot=shot, take_number=tn, camera=cam,
                            roll=f"{cam}{d:03d}", sound_roll=f"S{d:03d}",
                            clip_uri=f"gs://slateiq-dailies/{PROD}/d{d:02d}/{take_id}.mp4",
                            thumb_uri=f"gs://slateiq-dailies/{PROD}/d{d:02d}/{take_id}.jpg",
                            tc_in=tc(clock), duration_s=round(dur, 2), status=status,
                            director_note=rng.choice(DIRECTOR_NOTES),
                            lens_mm=rng.choice([18, 24, 27, 35, 40, 50, 65, 75, 100, 135]),
                            fps=FPS, iso=rng.choice([400, 800, 800, 1250, 2500]),
                            created_at=created)
                        takes.append(tk)
                        ev_seq = make_events(tk, sc, rng, nprng, events, ev_seq)
                        analyses.append(make_analysis(tk, sc, rng, nprng))
                    clock += dur + rng.uniform(35, 150)
                clock += rng.uniform(200, 900)  # relight / reset for next setup
    return takes, events, analyses


def make_events(tk, sc, rng, nprng, events, ev_seq):
    dur = tk["duration_s"]
    tid = tk["take_id"]

    def add(t0, t1, kind, speaker, text, flag="", sev=0, score=0.0, meta=""):
        nonlocal ev_seq
        ev_seq += 1
        events.append(dict(production_id=PROD, take_id=tid,
                           event_id=f"E{ev_seq:08d}", t_offset_s=round(float(t0), 2),
                           t_end_s=round(float(t1), 2), kind=kind, speaker=speaker,
                           text=text, flag_type=flag, severity=sev,
                           score=round(float(score), 3), meta=meta))

    add(0.0, 2.0, "slate", "", f"Scene {tk['scene_number']} {tk['shot']} take {tk['take_number']} "
        f"camera {tk['camera']}", meta='{"marker":"head"}')
    add(0.5, 1.5, "camera", "", f"{tk['lens_mm']}mm, ISO {tk['iso']}, {tk['fps']}fps",
        meta=f'{{"lens_mm":{tk["lens_mm"]},"iso":{tk["iso"]}}}')

    speakers = [c for c in sc["characters"] if c in LINE_BANK] or ["Thom"]
    n_lines = max(1, min(9, int(dur // 7)))
    t = 3.0
    for i in range(n_lines):
        if t > dur - 2:
            break
        sp = speakers[i % len(speakers)]
        line = rng.choice(LINE_BANK[sp])
        ln = min(rng.uniform(1.8, 4.5), max(1.0, dur - t - 1))
        add(t, t + ln, "dialogue", sp, line, score=round(rng.uniform(0.4, 0.95), 3))
        t += ln + rng.uniform(0.6, 2.6)
    for _ in range(rng.choice([1, 1, 2])):
        t0 = rng.uniform(1.0, max(1.5, dur - 3))
        add(t0, t0 + 1.5, "action", "", rng.choice(ACTIONS))
    lead = speakers[0]
    add(dur * 0.6, dur * 0.75, "emotion", lead, "peak emotional intensity",
        score=round(float(np.clip(nprng.beta(2.6, 2.2), 0.05, 0.99)), 3))

    flags = []
    for ftype, prob, (lo, hi) in FLAGS:
        p = prob * (1.7 if tk["status"] == "ng" else 1.0)
        if rng.random() < p:
            t0 = rng.uniform(0.5, max(1.0, dur - 3))
            span = rng.uniform(1.0, 4.0)
            sev = rng.randint(lo, hi)
            add(t0, min(dur, t0 + span), "flag", "", f"{ftype} detected", ftype, sev,
                score=round(rng.uniform(0.55, 0.99), 3))
            flags.append((ftype, t0, min(dur, t0 + span)))
    tk["_flags"] = flags
    return ev_seq


def make_analysis(tk, sc, rng, nprng):
    base = 0.82 if tk["status"] == "circled" else (0.45 if tk["status"] == "ng" else 0.66)
    q = float(np.clip(nprng.normal(base, 0.09), 0.05, 0.99))
    q -= 0.06 * len(tk.get("_flags", []))
    q = float(np.clip(q, 0.05, 0.99))
    speakers = [c for c in sc["characters"] if c in LINE_BANK] or ["Thom"]
    transcript = " ".join(f"{s}: {rng.choice(LINE_BANK[s])}" for s in speakers[:3])
    return dict(
        production_id=PROD, take_id=tk["take_id"],
        summary=(f"{sc['slug']} — {tk['shot']} setup, take {tk['take_number']}, "
                 f"cam {tk['camera']}, {tk['lens_mm']}mm. {sc['synopsis']}"),
        transcript=transcript,
        quality_score=round(q, 3),
        recommended=bool(tk["status"] == "circled" and q > 0.7),
        emotion_intensity=round(float(np.clip(nprng.beta(2.6, 2.2), 0.05, 0.99)), 3),
        performance_note=rng.choice(PERF_NOTES),
        model="gemini-3.5-flash",
        analyzed_at=tk["created_at"] + dt.timedelta(hours=rng.randint(2, 9)))


def build_continuity(takes, rng, n=60):
    by_scene = {}
    for t in takes:
        if t["status"] in ("circled", "hold"):
            by_scene.setdefault(t["scene_number"], []).append(t)
    scenes = [s for s, v in by_scene.items() if len(v) >= 2]
    rows = []
    for i in range(n):
        sn = scenes[i % len(scenes)]
        a, b = rng.sample(by_scene[sn], 2)
        cat = rng.choice(CONT_CATEGORIES)
        rows.append(dict(
            production_id=PROD, scene_number=sn,
            take_id_a=a["take_id"], take_id_b=b["take_id"], category=cat,
            description=CONT_DESCR[cat].format(a=a["take_id"], b=b["take_id"]),
            severity=rng.randint(1, 5),
            created_at=max(a["created_at"], b["created_at"]) + dt.timedelta(hours=3)))
    return rows


# ----------------------------------------------------------- telemetry (BIG)
def telemetry_chunks(takes, hz, nprng, rows_per_chunk=600_000):
    tid_buf, cols = [], [[] for _ in range(6)]
    n_buf = 0
    for tk in takes:
        n = max(4, int(tk["duration_s"] * hz))
        t = np.arange(n, dtype=np.float32) / hz
        ph = nprng.uniform(0, 6.28)
        focus = (0.86 + 0.06 * np.sin(t / 3.1 + ph)
                 + nprng.normal(0, 0.025, n)).astype(np.float32)
        expo = (nprng.normal(0, 0.28) + 0.18 * np.sin(t / 7.0 + ph)
                + nprng.normal(0, 0.05, n)).astype(np.float32)
        motion = np.clip(0.18 + 0.14 * np.sin(t / 2.3 + ph)
                         + np.abs(nprng.normal(0, 0.09, n)), 0, 1).astype(np.float32)
        rms = (-27.0 + 5.0 * np.sin(t / 1.7 + ph)
               + nprng.normal(0, 1.4, n)).astype(np.float32)
        peak = (rms + 9.0 + np.abs(nprng.normal(0, 2.0, n))).astype(np.float32)
        for ftype, t0, t1 in tk.get("_flags", []):
            m = (t >= t0) & (t <= t1)
            if not m.any():
                continue
            if ftype == "soft_focus":
                focus[m] -= 0.42
            elif ftype == "audio_clip":
                peak[m] = -0.4 + nprng.normal(0, 0.15, int(m.sum())).astype(np.float32)
                rms[m] += 8.0
            elif ftype in ("boom_in_shot", "crew_in_shot", "frame_edge"):
                motion[m] = np.clip(motion[m] + 0.3, 0, 1)
        np.clip(focus, 0.02, 1.0, out=focus)
        np.clip(peak, -60.0, 0.0, out=peak)
        np.clip(rms, -70.0, -1.0, out=rms)

        tid_buf.append((tk["take_id"], n))
        cols[0].append(t); cols[1].append(focus); cols[2].append(expo)
        cols[3].append(motion); cols[4].append(peak); cols[5].append(rms)
        n_buf += n
        if n_buf >= rows_per_chunk:
            yield _pack(tid_buf, cols)
            tid_buf, cols, n_buf = [], [[] for _ in range(6)], 0
    if n_buf:
        yield _pack(tid_buf, cols)


def _pack(tid_buf, cols):
    total = sum(n for _, n in tid_buf)
    tids = pa.DictionaryArray.from_arrays(
        pa.array(np.repeat(np.arange(len(tid_buf)), [n for _, n in tid_buf]), pa.int32()),
        pa.array([t for t, _ in tid_buf]))
    arrs = [np.concatenate(c) for c in cols]
    return pa.table({
        "production_id": pa.DictionaryArray.from_arrays(
            pa.array(np.zeros(total, dtype=np.int32)), pa.array([PROD])).cast(pa.string()),
        "take_id": tids.cast(pa.string()),
        "t_s": pa.array(arrs[0]), "focus_score": pa.array(arrs[1]),
        "exposure_ev": pa.array(arrs[2]), "motion": pa.array(arrs[3]),
        "audio_peak_db": pa.array(arrs[4]), "audio_rms_db": pa.array(arrs[5]),
    })


# ------------------------------------------------------------------- loading
def connect():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "clickhouse"),
        secure=os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true")


def run_schema(client, reset: bool):
    if reset:
        client.command("DROP DATABASE IF EXISTS slateiq SYNC")
    sql = open(os.path.join(HERE, "schema.sql")).read()
    for stmt in [s.strip() for s in sql.split(";\n") if s.strip()]:
        if stmt.lstrip().startswith("--") and "\n" not in stmt:
            continue
        client.command(stmt)


def insert(client, table, rows, cols):
    if not rows:
        return
    data = [[r[c] for c in cols] for r in rows]
    client.insert(f"slateiq.{table}", data, column_names=cols)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="drop & recreate slateiq")
    ap.add_argument("--telemetry-hz", type=float, default=25.0)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    t_start = time.time()
    rng = random.Random(args.seed)
    nprng = np.random.default_rng(args.seed)

    scenes = build_scenes(rng)
    scene_by_num = {s["scene_number"]: s for s in scenes}
    dates = shooting_dates(DAY12_DATE, PLANNED_DAYS)
    per_day = build_schedule(scenes, rng)
    days = build_days(per_day, scene_by_num, dates, rng)
    takes, events, analyses = build_takes(per_day, scene_by_num, dates, rng, nprng)
    cont = build_continuity(takes, rng)
    print(f"[gen] scenes={len(scenes)} days={len(days)} takes={len(takes)} "
          f"events={len(events)} analyses={len(analyses)} continuity={len(cont)} "
          f"({time.time() - t_start:.1f}s)")

    client = connect()
    run_schema(client, args.reset)

    insert(client, "production", [dict(
        production_id=PROD, title=TITLE, start_date=dates[1], planned_days=PLANNED_DAYS,
        director=DIRECTOR, dp=DP,
        notes=("Feature, 30 shooting days, Amsterdam. Day 12 is today; days 13-30 "
               "are scheduled but not shot. Sci-fi action drama, CC-BY source film."))],
           ["production_id", "title", "start_date", "planned_days", "director", "dp", "notes"])
    insert(client, "scene", scenes,
           ["production_id", "scene_number", "slug", "int_ext", "day_night",
            "page_eighths", "synopsis", "characters", "location", "script_day", "est_setups"])
    insert(client, "shooting_day", days,
           ["production_id", "day_number", "shoot_date", "unit", "call_time",
            "planned_wrap", "actual_wrap", "planned_scenes", "location", "weather", "notes"])
    insert(client, "take", takes,
           ["production_id", "take_id", "day_number", "scene_number", "shot",
            "take_number", "camera", "roll", "sound_roll", "clip_uri", "thumb_uri",
            "tc_in", "duration_s", "status", "director_note", "lens_mm", "fps",
            "iso", "created_at"])
    insert(client, "take_event", events,
           ["production_id", "take_id", "event_id", "t_offset_s", "t_end_s", "kind",
            "speaker", "text", "flag_type", "severity", "score", "meta"])
    insert(client, "take_analysis", analyses,
           ["production_id", "take_id", "summary", "transcript", "quality_score",
            "recommended", "emotion_intensity", "performance_note", "model", "analyzed_at"])
    insert(client, "continuity_note", cont,
           ["production_id", "scene_number", "take_id_a", "take_id_b", "category",
            "description", "severity", "created_at"])
    print(f"[load] dimension + event tables done ({time.time() - t_start:.1f}s)")

    total = 0
    for tbl in telemetry_chunks(takes, args.telemetry_hz, nprng):
        buf = io.BytesIO()
        pq.write_table(tbl, buf, compression="snappy")
        client.raw_insert("slateiq.frame_telemetry", insert_block=buf.getvalue(), fmt="Parquet")
        total += tbl.num_rows
        print(f"[load] frame_telemetry {total:,} rows ({time.time() - t_start:.1f}s)")

    print(f"[done] frame_telemetry={total:,} rows, total {time.time() - t_start:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
