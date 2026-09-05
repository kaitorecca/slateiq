#!/usr/bin/env python3
"""Step 3 — frame telemetry computed from the actual clip, at 25 Hz.

Two cheap ffmpeg passes per clip, both vectorised in numpy:

* video: decode to 160x?? gray rawvideo at 25 fps, then per 40 ms window
  - focus_score  = sqrt(Laplacian variance / FOCUS_REF), clamped to 0..1
  - exposure_ev  = log2(mean luma / 0.18 mid-grey), i.e. stops off mid-grey
  - motion       = mean abs frame-to-frame delta / MOTION_REF, clamped to 0..1
* audio: decode to mono float32 @ 8 kHz, then per 40 ms window
  - audio_peak_db / audio_rms_db in dBFS (<= 0, silence floored at -90)

The 25 rows/s rate and the 0..1 ranges match db/SCHEMA.md, so the golden
telemetry queries (e.g. "sustained soft focus: countIf(focus_score<0.55)/25")
give the right answer over real and synthetic takes alike.
"""

from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np

from config import FFMPEG, TAKES, Take

WIN = 0.04         # telemetry window, seconds (25 Hz, per db/SCHEMA.md)
VFPS = 25          # decode fps for the video pass
VW = 160           # decode width
ASR = 8000         # audio sample rate
DBFLOOR = -90.0

# calibration: Laplacian variance of a well-focused 160px-wide luma frame in
# this footage sits around 0.02-0.05; a gblur'd frame drops below 0.001.
# sqrt() compresses the top end so sharp takes spread over 0.6-1.0 and the
# soft-focus variants land near 0.15, either side of SCHEMA.md's 0.55 threshold.
FOCUS_REF = 0.035
MOTION_REF = 0.15  # mean abs inter-frame luma delta of a fast whip-pan

_LAP = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)


def _pipe(cmd: list[str]) -> bytes:
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[-2000:])
    return p.stdout


def _laplacian_var(frames: np.ndarray) -> np.ndarray:
    """Variance of a 4-neighbour Laplacian per frame, vectorised over N."""
    f = frames
    lap = (-4.0 * f[:, 1:-1, 1:-1]
           + f[:, :-2, 1:-1] + f[:, 2:, 1:-1]
           + f[:, 1:-1, :-2] + f[:, 1:-1, 2:])
    return lap.reshape(lap.shape[0], -1).var(axis=1)


def video_pass(clip, height_hint: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (focus, exposure_ev, motion) arrays sampled at VFPS."""
    # figure out the decoded frame height for the fixed width
    probe = json.loads(_pipe([
        FFMPEG.replace("ffmpeg", "ffprobe"), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(clip),
    ]).decode())["streams"][0]
    h = max(2, int(round(VW * probe["height"] / probe["width"] / 2)) * 2)

    raw = _pipe([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(clip),
        "-vf", f"fps={VFPS},scale={VW}:{h},format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ])
    n = len(raw) // (VW * h)
    frames = np.frombuffer(raw[: n * VW * h], dtype=np.uint8).reshape(n, h, VW).astype(np.float32) / 255.0
    if n == 0:
        return (np.zeros(0),) * 3

    focus = _laplacian_var(frames) if n else np.zeros(0)
    luma = frames.reshape(n, -1).mean(axis=1)
    motion = np.zeros(n, dtype=np.float32)
    if n > 1:
        motion[1:] = np.abs(np.diff(frames, axis=0)).reshape(n - 1, -1).mean(axis=1)
    return focus, luma, motion


def audio_pass(clip) -> np.ndarray:
    raw = _pipe([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(clip),
        "-vn", "-ac", "1", "-ar", str(ASR), "-f", "f32le", "-",
    ])
    return np.frombuffer(raw, dtype=np.float32)


def _windows(arr: np.ndarray, per_win: float, nwin: int):
    """Yield the slice of arr belonging to each 0.5 s window."""
    for i in range(nwin):
        a, b = int(i * per_win), int((i + 1) * per_win)
        yield arr[a:b] if b > a else arr[a:a + 1]


def telemetry_rows(t: Take, duration: float) -> list[tuple]:
    focus, luma, motion = video_pass(t.clip_path)
    audio = audio_pass(t.clip_path)
    nwin = max(1, int(duration / WIN))

    fscale = np.sqrt(np.maximum(focus, 0.0) / FOCUS_REF)

    rows: list[tuple] = []
    vper = VFPS * WIN
    aper = ASR * WIN
    fw = list(_windows(fscale, vper, nwin))
    lw = list(_windows(luma, vper, nwin))
    mw = list(_windows(motion, vper, nwin))
    aw = list(_windows(audio, aper, nwin))

    for i in range(nwin):
        f = float(np.clip(fw[i].mean() if fw[i].size else 0.0, 0.0, 1.0))
        mean_luma = float(lw[i].mean() if lw[i].size else 0.18)
        ev = float(np.clip(np.log2(max(mean_luma, 1e-4) / 0.18), -6, 6))
        mo = float(np.clip((mw[i].mean() if mw[i].size else 0.0) / MOTION_REF, 0.0, 1.0))
        chunk = aw[i]
        if chunk.size:
            peak = float(np.abs(chunk).max())
            rms = float(np.sqrt(np.mean(np.square(chunk, dtype=np.float64))))
        else:
            peak = rms = 0.0
        # dBFS: a lossy decode can overshoot 1.0, but a level meter cannot
        pdb = min(0.0, 20 * np.log10(peak)) if peak > 1e-5 else DBFLOOR
        rdb = min(0.0, 20 * np.log10(rms)) if rms > 1e-5 else DBFLOOR
        rows.append((round(i * WIN, 3), round(f, 4), round(ev, 3), round(mo, 4),
                     round(float(pdb), 2), round(float(rdb), 2)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="frame telemetry for day-12 clips")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    from clips import probe_duration

    for t in TAKES:
        if args.only and t.take_id not in args.only:
            continue
        rows = telemetry_rows(t, probe_duration(t.clip_path))
        arr = np.array([[r[1], r[2], r[3], r[4]] for r in rows])
        print(f"{t.take_id:<22} {len(rows):>4} rows  focus~{arr[:,0].mean():.3f} "
              f"soft_s={(arr[:,0]<0.55).sum()*WIN:5.1f} ev~{arr[:,1].mean():+.2f} "
              f"motion~{arr[:,2].mean():.3f} peak_max={arr[:,3].max():6.1f}dB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
