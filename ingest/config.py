"""Shared configuration for the SlateIQ ingest pipeline.

Owns the *real footage* slice of the dataset: shooting day 12 of production
``tos2026`` (Tears of Steel, Blender Foundation, CC-BY 3.0), scenes 12 / 14A /
27 / 33 / 41 / 56 / 78 / 102.  Everything else in the database is generated
synthetically by ``db/`` — see ``db/SCHEMA.md`` for the shared contract.

The take plan below is deliberately static (not re-derived from ffmpeg scene
detection at run time) so the whole pipeline is idempotent: same take ids, same
clip boundaries, same cache keys on every run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
FOOTAGE = DATA_DIR / "footage" / "tos.mp4"
CLIPS_DIR = DATA_DIR / "clips"
THUMBS_DIR = DATA_DIR / "thumbs"
CACHE_DIR = DATA_DIR / "cache"

FFMPEG = os.environ.get("FFMPEG_BIN", str(Path.home() / "miniconda3/envs/media/bin/ffmpeg"))
FFPROBE = os.environ.get("FFPROBE_BIN", str(Path.home() / "miniconda3/envs/media/bin/ffprobe"))

# --------------------------------------------------------------------------
# production constants
# --------------------------------------------------------------------------
PRODUCTION_ID = "tos2026"
DAY_NUMBER = 12
SHOOT_DATE = "2026-09-04"  # day 12 of the schedule; created_at anchors off this
REAL_SCENES = ["12", "14A", "27", "33", "41", "56", "78", "102"]

GEMINI_MODEL = os.environ.get("SLATEIQ_GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_FALLBACK_MODEL = "gemini-2.5-flash"

FLAG_TYPES = [
    "soft_focus",
    "boom_in_shot",
    "line_flub",
    "overlap",
    "continuity",
    "frame_edge",
    "audio_clip",
    "crew_in_shot",
]
EVENT_KINDS = ["dialogue", "action", "flag", "slate", "emotion", "camera"]
STATUSES = ["circled", "ng", "hold", "wild", "pending"]
CONTINUITY_CATEGORIES = ["wardrobe", "props", "hair_makeup", "screen_direction",
                         "lighting", "action_match", "dialogue", "set_dressing"]


@dataclass
class Take:
    """One dailies take backed by a real clip cut from the source footage."""

    scene_number: str
    shot: str
    take_number: int
    camera: str
    lens_mm: int
    iso: int
    tc_in: str
    status: str
    director_note: str
    # source-footage window (only for originals)
    src_start: float = 0.0
    src_end: float = 0.0
    # degradation variants
    parent: str | None = None
    degrade: str | None = None  # soft_focus | boom_in_shot | audio_clip | frame_edge
    # window inside the *clip* where the induced defect lives
    defect_window: tuple[float, float] = (0.0, 0.0)
    tags: list[str] = field(default_factory=list)

    @property
    def take_id(self) -> str:
        """db/SCHEMA.md id convention: TOS-D12-S<scene>-<setup>-<NN>-<camera>."""
        return (f"TOS-D{DAY_NUMBER:02d}-S{self.scene_number}-{self.shot}-"
                f"{self.take_number:02d}-{self.camera}")

    @property
    def is_variant(self) -> bool:
        return self.parent is not None

    @property
    def clip_path(self) -> Path:
        return CLIPS_DIR / f"{self.take_id}.mp4"

    @property
    def thumb_path(self) -> Path:
        return THUMBS_DIR / f"{self.take_id}.jpg"

    @property
    def clip_rel(self) -> str:
        return f"clips/{self.take_id}.mp4"

    @property
    def thumb_rel(self) -> str:
        return f"thumbs/{self.take_id}.jpg"


# --------------------------------------------------------------------------
# the take plan
#
# 18 original clips cut at ffmpeg scene-detection boundaries (gt(scene,0.35))
# from data/footage/tos.mp4, plus 6 degraded "bad take" variants that reuse
# their parent's Gemini analysis.  ~254 s of original footage is sent to
# Gemini, well inside the 12-minute budget.
# --------------------------------------------------------------------------
TAKES: list[Take] = [
    # ---- scene 12 -------------------------------------------------------
    Take("12", "A", 1, "A", 35, 800, "12:04:11:00", "circled",
         "Good energy, keep this one.", src_start=25.00, src_end=40.25),
    Take("12", "A", 2, "A", 35, 800, "12:05:02:12", "ng",
         "Focus puller lost her on the turn — NG.",
         parent="TOS-D12-S12-A-01-A", degrade="soft_focus", defect_window=(4.5, 9.5)),
    Take("12", "B", 1, "B", 50, 800, "12:19:40:06", "hold",
         "Alt angle, hold for editorial.", src_start=84.83, src_end=100.50),
    Take("12", "B", 2, "B", 50, 800, "12:26:18:20", "circled",
         "Cleaner. Print.", src_start=100.50, src_end=116.71),

    # ---- scene 14A ------------------------------------------------------
    Take("14A", "A", 1, "A", 28, 640, "13:02:55:14", "circled",
         "Nice reset on the walk-in.", src_start=119.88, src_end=139.92),
    Take("14A", "A", 2, "A", 28, 640, "13:09:31:02", "ng",
         "Boom dipped frame left — go again.",
         parent="TOS-D12-S14A-A-01-A", degrade="boom_in_shot", defect_window=(7.0, 8.6)),
    Take("14A", "B", 1, "B", 85, 640, "13:21:07:18", "pending",
         "Coverage, unreviewed.", src_start=145.79, src_end=158.54),

    # ---- scene 27 -------------------------------------------------------
    Take("27", "A", 1, "A", 40, 1250, "14:11:22:09", "circled",
         "That's the one — the beat lands.", src_start=158.54, src_end=172.29),
    Take("27", "A", 2, "A", 40, 1250, "14:17:48:23", "ng",
         "Sound reports clipping on the shout.",
         parent="TOS-D12-S27-A-01-A", degrade="audio_clip", defect_window=(5.0, 8.5)),
    Take("27", "B", 1, "B", 24, 1250, "14:33:05:11", "hold",
         "Wide, usable if we need the geography.", src_start=172.29, src_end=183.25),

    # ---- scene 33 -------------------------------------------------------
    Take("33", "A", 1, "A", 50, 400, "15:02:14:04", "circled",
         "Print it.", src_start=189.50, src_end=198.50),
    Take("33", "A", 2, "A", 50, 400, "15:07:59:16", "ng",
         "Operator drifted, she's clipping the frame edge.",
         parent="TOS-D12-S33-A-01-A", degrade="frame_edge", defect_window=(3.0, 7.0)),
    Take("33", "B", 1, "B", 100, 400, "15:19:33:02", "pending",
         "Insert / detail pass.", src_start=225.08, src_end=234.58),

    # ---- scene 41 -------------------------------------------------------
    Take("41", "A", 1, "A", 32, 1600, "16:04:41:19", "circled",
         "Strong. Emotion is there.", src_start=238.67, src_end=253.42),
    Take("41", "A", 2, "A", 32, 1600, "16:12:26:07", "ng",
         "Soft through the middle — NG for focus.",
         parent="TOS-D12-S41-A-01-A", degrade="soft_focus", defect_window=(3.5, 9.0)),
    Take("41", "B", 1, "B", 65, 1600, "16:29:18:21", "hold",
         "Long lens option, hold.", src_start=257.92, src_end=276.50),

    # ---- scene 56 -------------------------------------------------------
    Take("56", "A", 1, "A", 21, 500, "17:08:03:13", "circled",
         "Great movement, keep.", src_start=276.50, src_end=295.12),
    Take("56", "B", 1, "B", 50, 500, "17:22:47:05", "pending",
         "Second unit style coverage.", src_start=330.29, src_end=338.92),
    Take("56", "B", 2, "B", 50, 500, "17:26:12:18", "ng",
         "Boom shadow / boom in frame top.",
         parent="TOS-D12-S56-B-01-B", degrade="boom_in_shot", defect_window=(3.0, 4.8)),

    # ---- scene 78 -------------------------------------------------------
    Take("78", "A", 1, "A", 35, 2000, "18:03:55:00", "circled",
         "Print. Best of the three.", src_start=444.88, src_end=461.79),
    Take("78", "B", 1, "B", 75, 2000, "18:15:22:14", "hold",
         "Tighter option.", src_start=468.33, src_end=480.21),
    Take("78", "C", 1, "A", 18, 2000, "18:31:09:22", "pending",
         "Wide establishing, unreviewed.", src_start=489.42, src_end=502.38),

    # ---- scene 102 ------------------------------------------------------
    Take("102", "A", 1, "A", 40, 1000, "19:06:30:11", "circled",
         "Final of the day — got it.", src_start=543.17, src_end=556.83),
    Take("102", "B", 1, "B", 28, 1000, "19:24:58:03", "hold",
         "Safety take.", src_start=564.29, src_end=588.00),
]

TAKES_BY_ID = {t.take_id: t for t in TAKES}
ORIGINALS = [t for t in TAKES if not t.is_variant]
VARIANTS = [t for t in TAKES if t.is_variant]

# camera roll / sound roll are per (day, camera) on a real set
ROLL = {"A": "A012", "B": "B012"}
SOUND_ROLL = {"A": "S012", "B": "S012"}
FPS = 24  # Tears of Steel is 24 fps; the synthetic units shoot 25


def roll_for(t: Take) -> str:
    return ROLL[t.camera]


def sound_roll_for(t: Take) -> str:
    return SOUND_ROLL[t.camera]


def scene_takes(scene: str) -> list[Take]:
    return [t for t in TAKES if t.scene_number == scene]
