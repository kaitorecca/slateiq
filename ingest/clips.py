#!/usr/bin/env python3
"""Step 1 — cut day-12 dailies clips out of the source footage.

* originals: straight cuts at ffmpeg scene-detection boundaries, re-encoded to
  720p h264 + faststart so they stream from GCS/Caddy without a seek round-trip
* variants: the same footage run through a deliberate degradation so the
  dataset contains realistic NG takes (soft focus, boom in shot, audio
  clipping, frame-edge drift)
* thumbnails: one jpg per take, grabbed ~25% into the clip

Idempotent: a clip/thumb that already exists is left alone unless --force.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from config import (
    CLIPS_DIR,
    FFMPEG,
    FFPROBE,
    FOOTAGE,
    ORIGINALS,
    TAKES,
    TAKES_BY_ID,
    THUMBS_DIR,
    VARIANTS,
    Take,
)

V_ENC = [
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "26",
    "-pix_fmt",
    "yuv420p",
    "-profile:v",
    "high",
    "-g",
    "48",
    "-c:a",
    "aac",
    "-b:a",
    "96k",
    "-ac",
    "2",
    "-ar",
    "48000",
    "-movflags",
    "+faststart",
]
SCALE = "scale=1280:-2"


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-4000:])
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd[:6])} ...")


def probe_duration(path) -> float:
    out = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return float(out)


def cut_original(t: Take) -> None:
    dur = round(t.src_end - t.src_start, 3)
    run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{t.src_start:.3f}",
            "-i",
            str(FOOTAGE),
            "-t",
            f"{dur:.3f}",
            "-vf",
            SCALE,
            *V_ENC,
            str(t.clip_path),
        ]
    )


def variant_filters(t: Take) -> tuple[str, str]:
    """Return (video_filter, audio_filter) implementing the degradation."""
    a, b = t.defect_window
    if t.degrade == "soft_focus":
        return (f"{SCALE},gblur=sigma=14:steps=2:enable='between(t,{a},{b})'", "anull")
    if t.degrade == "boom_in_shot":
        # a black boom silhouette dipping in from the top of frame over ~0.5 s
        box = (
            "drawbox=x=iw*0.34:w=iw*0.17:h=ih*0.16:"
            f"y='ih*0.16*(-1+min(1,(t-{a})/0.5))':color=black@1.0:t=fill:"
            f"enable='between(t,{a},{b})'"
        )
        return (f"{SCALE},{box}", "anull")
    if t.degrade == "audio_clip":
        # +20 dB into hard clipping across the window
        return (SCALE, f"volume=enable='between(t,{a},{b})':volume=10.0")
    if t.degrade == "frame_edge":
        # slow reframe drift: punch in 12% and pan, subject creeps to the edge
        crop = (
            "crop=w=floor(iw*0.88/2)*2:h=floor(ih*0.88/2)*2:"
            "x='(iw-ow)*min(1,max(0,t/8))':y='(ih-oh)*0.5'"
        )
        return (f"{crop},{SCALE}", "anull")
    raise ValueError(f"unknown degradation {t.degrade!r}")


def make_variant(t: Take) -> None:
    parent = TAKES_BY_ID[t.parent]
    vf, af = variant_filters(t)
    run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(parent.clip_path),
            "-vf",
            vf,
            "-af",
            af,
            *V_ENC,
            str(t.clip_path),
        ]
    )


def make_thumb(t: Take) -> None:
    dur = probe_duration(t.clip_path)
    run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{dur * 0.25:.2f}",
            "-i",
            str(t.clip_path),
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-2",
            "-q:v",
            "4",
            str(t.thumb_path),
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="cut day-12 dailies clips")
    ap.add_argument("--force", action="store_true", help="re-encode existing clips")
    args = ap.parse_args()

    if not FOOTAGE.exists():
        raise SystemExit(f"missing source footage {FOOTAGE}")
    if not shutil.which(FFMPEG) and not FFMPEG.startswith("/"):
        raise SystemExit(f"ffmpeg not found at {FFMPEG}")
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    total = 0.0
    for t in ORIGINALS:
        if args.force or not t.clip_path.exists():
            cut_original(t)
            print(f"  cut  {t.take_id:<14} {t.src_start:7.2f}->{t.src_end:7.2f}")
        total += t.src_end - t.src_start
    for t in VARIANTS:
        if args.force or not t.clip_path.exists():
            make_variant(t)
            print(f"  degr {t.take_id:<14} {t.degrade}")
    for t in TAKES:
        if args.force or not t.thumb_path.exists():
            make_thumb(t)

    sizes = sum(t.clip_path.stat().st_size for t in TAKES) / 1e6
    print(
        f"{len(TAKES)} clips ({len(ORIGINALS)} original + {len(VARIANTS)} variant), "
        f"{total:.0f}s of original footage to analyse, {sizes:.1f} MB on disk"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
