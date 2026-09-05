"""Pydantic response schema for the Gemini dailies-analysis call.

Kept in its own module so ``analyze.py``, ``continuity.py`` and ``load.py``
all agree on the shape of the cached JSON in ``data/cache/``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FlagType = Literal[
    "soft_focus",
    "boom_in_shot",
    "line_flub",
    "overlap",
    "continuity",
    "frame_edge",
    "audio_clip",
    "crew_in_shot",
]


class TranscriptSegment(BaseModel):
    start: float = Field(description="seconds from the start of the clip")
    end: float
    speaker: str = Field(description="best-guess character or 'UNKNOWN'")
    text: str


class ActionBeat(BaseModel):
    start: float
    end: float
    text: str = Field(description="what physically happens, present tense")


class QualityFlag(BaseModel):
    type: FlagType
    start: float
    end: float
    severity: int = Field(ge=1, le=3, description="1 minor, 2 notable, 3 unusable")
    evidence: str


class EmotionBeat(BaseModel):
    start: float
    end: float
    intensity: float = Field(ge=0.0, le=1.0)
    label: str = Field(description="one word, e.g. grief, defiance, calm")


class CameraNote(BaseModel):
    start: float
    end: float
    text: str = Field(description="camera move / framing, e.g. 'slow push in'")


class TakeAnalysis(BaseModel):
    slate: str = Field(description="what the slate says, or '' if no slate visible")
    summary: str = Field(description="2-3 sentences describing the take")
    transcript: list[TranscriptSegment]
    actions: list[ActionBeat]
    flags: list[QualityFlag]
    emotions: list[EmotionBeat]
    camera: list[CameraNote]
    quality_score: float = Field(ge=0.0, le=10.0)
    recommended: bool
    performance_note: str


class ContinuityItem(BaseModel):
    take_id_a: str
    take_id_b: str
    category: Literal["wardrobe", "props", "hair_makeup", "screen_direction",
                      "lighting", "action_match", "dialogue", "set_dressing"]
    description: str
    severity: int = Field(ge=1, le=3)


class ContinuityReport(BaseModel):
    notes: list[ContinuityItem]
