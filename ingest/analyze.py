#!/usr/bin/env python3
"""Step 2 — Gemini multimodal analysis of each ORIGINAL dailies clip.

Uploads the clip through the Gemini File API, asks for a strict JSON document
(pydantic ``TakeAnalysis`` as ``response_schema``) and caches the raw result at
``data/cache/<sha1 of clip>.json`` so re-runs are free.

Degraded variants are never sent to Gemini: they reuse their parent's analysis,
and ``load.py`` injects the induced flag + a lowered quality score.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from config import CACHE_DIR, GEMINI_MODEL, ORIGINALS, Take
from gemini import cache_get, cache_put, client, generate, sha1_file, token_report, upload_active
from schema_models import TakeAnalysis

PROMPT = """You are a script supervisor and DIT reviewing a single unedited camera
take from a feature film's dailies. Watch and listen to the whole clip.

Return JSON only, matching the provided schema. Rules:
- All timestamps are SECONDS FROM THE START OF THIS CLIP, floats, never beyond
  the clip duration ({duration:.1f}s).
- transcript: one segment per continuous line of dialogue. If nobody speaks,
  return an empty list. Guess the speaker from who is on screen / voice
  ("MAN", "WOMAN", "CELIA", "THOM", "NARRATOR", ...); use "UNKNOWN" if unsure.
  Transcribe what is actually said, do not invent lines.
- actions: the physical beats a script supervisor would log (entrances, props
  handled, hits, exits).
- flags: technical problems ONLY if you actually observe them. Allowed types:
  soft_focus, boom_in_shot, line_flub, overlap, continuity, frame_edge,
  audio_clip, crew_in_shot. severity 1 = minor, 2 = notable, 3 = unusable.
  Cite what you saw/heard in `evidence`. An empty list is a valid, good answer.
- emotions: the emotional temperature of the performance over time, intensity
  0..1, one-word label.
- camera: framing and camera-move notes.
- slate: read the clapper slate if one is visible, otherwise "".
- quality_score 0..10 judges this take as a usable performance + technically
  clean image and sound. recommended = would you circle this take.
- performance_note: one or two sentences of direction-facing feedback.
"""


def analyse_clip(cl, t: Take, duration: float, model: str) -> dict:
    key = sha1_file(t.clip_path)
    cached = cache_get(key)
    if cached is not None:
        return cached

    print(f"  upload {t.take_id} ({t.clip_path.stat().st_size/1e6:.1f} MB)")
    f = upload_active(cl, t.clip_path)
    cfg = {
        "response_mime_type": "application/json",
        "response_schema": TakeAnalysis,
        "temperature": 0.3,
    }
    t0 = time.time()
    resp, used = generate(
        cl,
        contents=[f, PROMPT.format(duration=duration)],
        config=cfg,
        model=model,
    )
    data = json.loads(resp.text)
    TakeAnalysis.model_validate(data)  # fail loudly on a bad shape
    payload = {
        "take_id": t.take_id,
        "clip_sha1": key,
        "model": used,
        "duration_s": duration,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "analysis": data,
    }
    cache_put(key, payload)
    try:
        cl.files.delete(name=f.name)
    except Exception:  # noqa: BLE001 - best effort cleanup
        pass
    print(f"    ok in {time.time()-t0:.1f}s  score={data['quality_score']} "
          f"flags={[fl['type'] for fl in data['flags']]}")
    return payload


def load_cached(t: Take) -> dict | None:
    """Cached analysis for a take (variants fall back to their parent's clip)."""
    return cache_get(sha1_file(t.clip_path))


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini analysis of day-12 dailies clips")
    ap.add_argument("--model", default=GEMINI_MODEL)
    ap.add_argument("--only", nargs="*", help="restrict to these take ids")
    ap.add_argument("--dry-run", action="store_true", help="report cache state, call nothing")
    args = ap.parse_args()

    from clips import probe_duration

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    todo = [t for t in ORIGINALS if not args.only or t.take_id in args.only]
    missing = [t for t in todo if cache_get(sha1_file(t.clip_path)) is None]
    secs = sum(probe_duration(t.clip_path) for t in missing)
    print(f"{len(todo)} original clips, {len(missing)} uncached "
          f"({secs/60:.1f} min of video to send to {args.model})")
    if args.dry_run:
        return 0
    if secs > 12 * 60:
        raise SystemExit("refusing to analyse more than 12 minutes of footage")

    cl = client()
    for t in todo:
        try:
            analyse_clip(cl, t, probe_duration(t.clip_path), args.model)
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {t.take_id}: {exc}", file=sys.stderr)
    print(token_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
