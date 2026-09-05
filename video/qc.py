#!/usr/bin/env python3
"""QC the rendered trailer: duration, streams, and five checkpoint frames.

    .venv/bin/python video/qc.py [path/to.mp4]

Prints a pass/fail table and writes the checkpoint stills to data/video/qc/ so a
human (or an agent with eyes) can confirm no frame is blank, loading or illegible.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FFMPEG = os.environ.get("FFMPEG", str(Path.home() / "miniconda3/envs/media/bin/ffmpeg"))
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")

CEILING = 180.0


def sh(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main() -> int:
    mp4 = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "video" / "slateiq_trailer.mp4"
    if not mp4.exists():
        sys.exit(f"no such render: {mp4}")

    info = json.loads(sh([FFPROBE, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(mp4)]))
    fmt = info["format"]
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(fmt["duration"])
    size_mb = int(fmt["size"]) / 1e6

    checks = [
        ("duration ≤ 3:00", dur <= CEILING, f"{int(dur // 60)}:{dur % 60:04.1f}"),
        ("1920×1080", (v["width"], v["height"]) == (1920, 1080), f'{v["width"]}x{v["height"]}'),
        ("30 fps", v["r_frame_rate"] in ("30/1", "30000/1001"), v["r_frame_rate"]),
        ("h264", v["codec_name"] == "h264", v["codec_name"]),
        ("aac audio present", a is not None and a["codec_name"] == "aac", a["codec_name"] if a else "NONE"),
        ("audio not silent", a is not None and float(a.get("duration", 0)) > dur * 0.9,
         f'{float(a.get("duration", 0)):.1f}s' if a else "—"),
    ]

    # mean volume is the cheap proof that the voiceover actually made it in
    out = subprocess.run([FFMPEG, "-v", "info", "-i", str(mp4), "-af", "volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    mean = next((l.split("mean_volume:")[1].strip() for l in out.splitlines() if "mean_volume:" in l), "?")
    checks.append(("voiceover audible", "-" in mean and float(mean.split()[0]) > -40, f"mean {mean}"))

    qc = ROOT / "data" / "video" / "qc"
    qc.mkdir(parents=True, exist_ok=True)
    points = [dur * f for f in (0.08, 0.28, 0.48, 0.70, 0.94)]
    for i, t in enumerate(points, 1):
        subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4),
                        "-frames:v", "1", "-vf", "scale=1280:-1", str(qc / f"cp{i}_{t:.0f}s.png")], check=True)

    width = max(len(n) for n, _, _ in checks)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print(f"\n  size {size_mb:.1f} MB")
    print(f"  checkpoint stills → {qc.relative_to(ROOT)}/ (inspect all five)")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
