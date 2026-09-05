#!/usr/bin/env python3
"""Cut the SlateIQ trailer from the captured scenes + the Gemini TTS voiceover.

    .venv/bin/python video/build.py            # full render
    .venv/bin/python video/build.py --fast     # ultrafast preset, for iterating

Inputs   data/video/raw/*.webm      (video/capture.mjs)
         data/video/vo/*.wav        (video/tts.py)
Outputs  data/video/slateiq_trailer.mp4        1920x1080 / 30 fps / h264 + aac
         video/slateiq_trailer_720p.mp4        <=25 MB, committed for upload
         video/CAPTIONS.srt

Every segment is pinned to the length of its own voiceover clip: sub-clips are
trimmed to fit, and if a scene came up short its last frame is held rather than
letting the picture run out from under the narration.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "video" / "raw"
VO = ROOT / "data" / "video" / "vo"
WORK = ROOT / "data" / "video" / "work"
OUT = ROOT / "data" / "video" / "slateiq_trailer.mp4"
OUT720 = ROOT / "video" / "slateiq_trailer_720p.mp4"
SRT = ROOT / "video" / "CAPTIONS.srt"

FFMPEG = os.environ.get("FFMPEG", str(Path.home() / "miniconda3/envs/media/bin/ffmpeg"))
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H, FPS = 1920, 1080, 30
VO_TEMPO = 1.06      # imperceptible tighten; buys ~10 s against the 3:00 ceiling
GAP = 0.30           # breath between beats
LEAD = 1.70          # slate + title before the first line of narration
TAIL = 3.00          # hold on the end card after the last word
COLD = 1.80          # each of the three cold-open stills


@dataclass
class Clip:
    """One piece of source footage inside a beat."""
    src: str
    start: float
    dur: float
    speed: float = 1.0                    # >1 speeds the shot up (eats agent wait time)
    crop: tuple[int, int, int, int] | None = None   # w,h,x,y — punch in on a detail
    freeze: bool = False                  # hold one frame from `start` for `dur` (cold open)


@dataclass
class Beat:
    vo: str | None            # voiceover id, or None for a silent segment
    clips: list[Clip]
    caption: list[str] = field(default_factory=list)


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True, **kw)


def probe(path: Path) -> float:
    """Real duration of a Playwright webm — its container duration is unreliable."""
    out = sh([FFPROBE, "-v", "error", "-count_frames", "-select_streams", "v:0",
              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)]).stdout
    return int(out.strip().splitlines()[0]) / 25.0


def wav_dur(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


# --------------------------------------------------------------------- the cut

def timeline(manifest: dict, marks: dict) -> list[Beat]:
    d = {k: v["dur"] / VO_TEMPO for k, v in manifest.items()}
    hero = marks.get("hero", {})
    dpr = marks.get("dpr", {})
    live = marks.get("live", {})
    hl = marks.get("health", {})
    return [
        # cold open: the proof, before anyone says a word.
        # three real frames out of the captured footage — the clickhouse-client
        # benchmark, the full-frame mcp-clickhouse trace, and the take itself.
        Beat(None,
             [Clip("terminal", 11.6, COLD, freeze=True),
              Clip("hero", hero.get("traceIn", 40.8) + 1.8, COLD, freeze=True),
              Clip("hero", hero.get("takeIn", 49.0) + 1.6, COLD, freeze=True,
                   crop=(1000, 562, 460, 420))],
             caption=["A circled take with 13 seconds of soft focus.",
                      "Found in 65 milliseconds."]),
        # the slate claps and the title lands before anyone speaks
        Beat(None, [Clip("title", 0.0, LEAD)]),
        Beat("b01", [Clip("title", LEAD, d["b01"])]),
        Beat("b02", [Clip("cost", 0.2, d["b02"])]),
        Beat("b03", [Clip("ingest", 0.4, d["b03"])]),
        # the hero beat: answer -> full-frame MCP trace -> the clip -> the raw query
        # answer on screen -> the full-frame mcp-clickhouse trace -> the clip -> the raw query
        Beat("b04", [Clip("hero", hero.get("answered", 0) + 0.8, 18.0),
                     Clip("terminal", 1.4, d["b04"] - 18.0)]),
        Beat("b05", [Clip("editor", "ANSWER-3", 11.0),
                     Clip("producer", "ANSWER-3", d["b05"] - 11.0)]),
        Beat("b06", [Clip("continuity", "ANSWER-2", d["b06"])]),
        Beat("b07", [Clip("dpr", max(0.0, dpr.get("report", 5.0) - 1.0), d["b07"])]),
        # Grafana on the hosted service (where /api/config wires it up), then the
        # takes browser with the flag timeline open
        Beat("b08", [Clip("health", hl.get("charts", 4.0) + 0.6, 6.6),
                     Clip("health", hl.get("takes", 32.0) + 6.7, d["b08"] - 6.6)]),
        # the closing beat has to show the hosted Cloud Run URL, legible, for >3 s
        Beat("b09", [Clip("arch", 0.3, 9.8), Clip("live", live.get("urls", 9.0) - 0.4, d["b09"] - 9.8,
                          crop=(1160, 653, 500, 540))]),
        Beat("b10", [Clip("end", 0.0, d["b10"] + TAIL)]),
    ]


def resolve_start(clip: Clip, src_dur: float) -> float:
    """Symbolic in-points, so the cut survives a re-capture of different length.

    ANSWER-n  -> n seconds of lead-in before the end of the scene (the agent has
                 answered by then; the typing and the wait are not the story).
    TAIL      -> as late as the shot allows.
    HERO_IN   -> positioned so the full-frame trace hold lands inside the beat.
    """
    if isinstance(clip.start, (int, float)):
        return float(clip.start)
    if clip.start == "TAIL":
        return max(0.0, src_dur - clip.dur - 0.4)
    if clip.start == "HERO_IN":
        return max(0.0, src_dur - clip.dur - 0.6)
    if clip.start.startswith("ANSWER-"):
        lead = float(clip.start.split("-")[1])
        return max(0.0, src_dur - clip.dur - lead)
    raise ValueError(clip.start)


def render_clip(clip: Clip, dst: Path, fast: bool) -> None:
    src = RAW / f"{clip.src}.webm"
    if not src.exists():
        sys.exit(f"missing footage: {src}")
    src_dur = probe(src)
    start = resolve_start(clip, src_dur)
    have = max(0.0, (src_dur - start) / clip.speed)
    need = clip.dur

    if clip.freeze:
        # one real frame, held — the cold open is a stack of evidence stills, not
        # motion, and freezing keeps them readable at 1.8 s apiece.
        still = dst.with_suffix(".png")
        sh([FFMPEG, "-y", "-v", "error", "-ss", f"{min(start, max(0.0, src_dur - 0.1)):.3f}",
            "-i", str(src), "-frames:v", "1", str(still)])
        svf = []
        if clip.crop:
            svf.append("crop={}:{}:{}:{}".format(*clip.crop))
        svf += [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black", "setsar=1", f"fps={FPS}"]
        sh([FFMPEG, "-y", "-v", "error", "-loop", "1", "-t", f"{need:.3f}", "-i", str(still),
            "-vf", ",".join(svf), "-an", "-c:v", "libx264",
            "-preset", "ultrafast" if fast else "medium", "-crf", "16",
            "-pix_fmt", "yuv420p", str(dst)])
        return

    vf = [f"fps={FPS}"]
    if clip.crop:
        vf.append("crop={}:{}:{}:{}".format(*clip.crop))
    vf += [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black", "setsar=1"]
    if clip.speed != 1.0:
        vf.insert(0, f"setpts=PTS/{clip.speed}")
    if have < need - 0.05:
        # scene came up short — freeze its last frame rather than cutting the VO
        vf.append(f"tpad=stop_mode=clone:stop_duration={need - have + 0.2:.3f}")

    sh([FFMPEG, "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(src),
        "-vf", ",".join(vf), "-t", f"{need:.3f}",
        "-an", "-c:v", "libx264", "-preset", "ultrafast" if fast else "medium",
        "-crf", "16", "-pix_fmt", "yuv420p", str(dst)])


# ------------------------------------------------------------------- captions

# The VO text spells acronyms out so Gemini TTS says the letters; the caption
# should show the acronym the way a human writes it.
CAPTION_FIXES = {"M C P": "MCP", "P D F": "PDF", "N G": "NG"}


def split_caption(text: str, max_chars: int = 62) -> list[str]:
    """Break a beat into caption lines on sentence, then clause, then width.

    Sentence splitting must not fire inside an abbreviation ("One a.m. On every
    film set…"), and a long sentence must flush whatever is already buffered
    before it emits its own fragments — otherwise lines from different sentences
    get spliced together and the caption says something nobody said.
    """
    import re

    for spoken, written in CAPTION_FIXES.items():
        text = text.replace(spoken, written)
    abbr = re.compile(r"\b[A-Za-z]\.$")
    sentences: list[str] = []
    for chunk in re.split(r"(?<=[.:?!])\s+", text.strip()):
        if sentences and abbr.search(sentences[-1]):
            sentences[-1] = f"{sentences[-1]} {chunk}"
        else:
            sentences.append(chunk)

    lines: list[str] = []
    buf = ""
    for sent in sentences:
        if len(sent) <= max_chars:
            if buf and len(buf) + 1 + len(sent) <= max_chars:
                buf = f"{buf} {sent}"
            else:
                if buf:
                    lines.append(buf)
                buf = sent
            continue
        if buf:
            lines.append(buf)
            buf = ""
        # Balanced wrap: aim for equal-width lines so a long sentence never ends
        # on a one-word orphan sitting alone at the bottom of the frame.
        n = math.ceil(len(sent) / max_chars)
        width = min(max_chars, math.ceil(len(sent) / n) + 4)
        cur = ""
        for word in sent.split():
            if cur and len(cur) + 1 + len(word) > width:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}".strip()
        buf = cur
    if buf:
        lines.append(buf)
    return [x for x in lines if x]


def ts(t: float, sep: str = ",") -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def ass_ts(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def build_captions(cues: list[tuple[float, float, str]]) -> tuple[str, str]:
    srt = "\n".join(
        f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n" for i, (a, b, text) in enumerate(cues, 1)
    )
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap, DejaVu Sans, 44, &H00F2F0EC, &H00000000, &HB4000000, -1, 3, 0, 0, 2, 200, 200, 62, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "\n".join(
        f"Dialogue: 0,{ass_ts(a)},{ass_ts(b)},Cap,,0,0,0,,{text}" for a, b, text in cues
    )
    return srt, head + body + "\n"


# ----------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="ultrafast x264, for iterating on the cut")
    args = ap.parse_args()

    manifest = json.loads((VO / "manifest.json").read_text())
    mpath = RAW / "markers.json"
    marks = json.loads(mpath.read_text()) if mpath.exists() else {}
    beats = timeline(manifest, marks)
    WORK.mkdir(parents=True, exist_ok=True)
    for stale in WORK.glob("*"):
        stale.unlink()

    # ---- picture -----------------------------------------------------------
    pieces, t, cues, audio_bits = [], 0.0, [], []
    for bi, beat in enumerate(beats):
        seg_start = t
        for ci, clip in enumerate(beat.clips):
            dst = WORK / f"{bi:02d}_{ci}_{clip.src}.mp4"
            render_clip(clip, dst, args.fast)
            pieces.append(dst)
            t += clip.dur
        if beat.vo:
            vo_len = manifest[beat.vo]["dur"] / VO_TEMPO
            audio_bits.append((beat.vo, seg_start, vo_len))
            lines = split_caption(manifest[beat.vo]["text"])
            total_chars = sum(len(x) for x in lines)
            ct = seg_start
            for line in lines:
                span = vo_len * len(line) / total_chars
                cues.append((ct, ct + span, line))
                ct += span
        elif beat.caption:
            # a silent beat that still carries a card (the cold open) captions itself
            seg_len = sum(c.dur for c in beat.clips)
            total_chars = sum(len(x) for x in beat.caption)
            ct = seg_start
            for line in beat.caption:
                span = seg_len * len(line) / total_chars
                cues.append((ct, ct + span, line))
                ct += span
        if bi < len(beats) - 1:
            # a beat of black between segments keeps the cuts from feeling rushed
            gap = WORK / f"{bi:02d}_gap.mp4"
            sh([FFMPEG, "-y", "-v", "error", "-f", "lavfi",
                "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={GAP}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
                "-pix_fmt", "yuv420p", str(gap)])
            pieces.append(gap)
            t += GAP

    total = t
    print(f"picture: {total:.1f}s ({int(total // 60)}:{total % 60:04.1f})")
    if total > 180:
        print(f"!! over the 3:00 ceiling by {total - 180:.1f}s", file=sys.stderr)

    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in pieces))

    # ---- captions ----------------------------------------------------------
    srt, ass = build_captions(cues)
    SRT.write_text(srt)
    ass_path = WORK / "captions.ass"
    ass_path.write_text(ass)

    # ---- voiceover, laid onto a silent bed at the right offsets -------------
    inputs, filters, labels = ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"], [], []
    for i, (bid, at, _len) in enumerate(audio_bits, start=1):
        inputs += ["-i", str(VO / f"{bid}.wav")]
        filters.append(
            f"[{i}:a]atempo={VO_TEMPO},aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={int(at * 1000)}|{int(at * 1000)}[a{i}]"
        )
        labels.append(f"[a{i}]")
    filters.append(
        "[0:a]" + "".join(labels) + f"amix=inputs={len(labels) + 1}:normalize=0:dropout_transition=0"
        ",dynaudnorm=f=200:g=5:p=0.62,alimiter=limit=0.94[aout]"
    )
    voice = WORK / "voice.m4a"
    sh([FFMPEG, "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(voice)])

    # ---- master ------------------------------------------------------------
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sh([FFMPEG, "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(voice),
        "-vf", f"ass={ass_path},fade=t=in:st=0:d=0.6,fade=t=out:st={total - 1.0:.2f}:d=1.0",
        "-map", "0:v", "-map", "1:a", "-shortest",
        "-c:v", "libx264", "-preset", "ultrafast" if args.fast else "slow",
        "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-profile:v", "high", "-level", "4.0", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(OUT)])

    # ---- 720p upload copy, kept under 25 MB --------------------------------
    OUT720.parent.mkdir(parents=True, exist_ok=True)
    for crf in (23, 26, 29, 32):
        sh([FFMPEG, "-y", "-v", "error", "-i", str(OUT),
            "-vf", "scale=1280:720", "-c:v", "libx264", "-preset", "slow",
            "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "128k", str(OUT720)])
        mb = OUT720.stat().st_size / 1e6
        print(f"720p @ crf {crf}: {mb:.1f} MB")
        if mb <= 25:
            break

    print(f"\nmaster {OUT}  {OUT.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
