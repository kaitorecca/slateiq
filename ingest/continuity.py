#!/usr/bin/env python3
"""Step 4 — cross-take continuity notes, one cheap text-only Gemini call per scene.

For every scene that has 2+ takes we hand Gemini the *already computed* JSON
analyses (transcript, actions, camera notes) and ask what a script supervisor
would flag between takes: props, wardrobe, eyeline, line variations, action
mismatches, lighting. No video is re-sent, so this costs a few thousand text
tokens per scene.

Results are cached at ``data/cache/<sha1 of the prompt>.json``.
"""

from __future__ import annotations

import argparse
import json

from config import REAL_SCENES, scene_takes
from gemini import cache_get, cache_put, client, generate, sha1_text, token_report
from schema_models import ContinuityReport

PROMPT = """You are the script supervisor on a feature film. Below are the JSON
analyses of every take shot today for scene {scene}. Each take is a separate
camera setup or a repeat of the same setup.

Compare the takes against each other and report genuine CONTINUITY
DISCREPANCIES an editor would trip over when cutting them together:
- props: an object present/absent/moved/held in the other hand
- set_dressing: something in the set itself moved, added or removed
- wardrobe: clothing, blood, dirt, sleeves
- hair_makeup: hair, beard, makeup, sweat, wounds
- screen_direction: eyelines or movement pointing inconsistent ways across the cut
- dialogue: the same scripted line delivered with different words
- action_match: a physical beat performed differently or at a different point
- lighting: visible change in light level, direction or colour

Rules:
- Only report differences you can actually justify from the supplied analyses.
  If two takes are consistent, say nothing about them. An empty list is a
  perfectly good answer.
- take_id_a and take_id_b MUST be two different ids from this exact list:
  {ids}
- severity 1 = editorially invisible, 2 = noticeable, 3 = unusable together.
- description: one concrete sentence naming both takes' behaviour.

TAKES:
{blob}
"""


def scene_payload(scene: str) -> tuple[list[str], str] | None:
    from analyze import load_cached

    takes = scene_takes(scene)
    if len(takes) < 2:
        return None
    ids, blocks = [], []
    for t in takes:
        cached = load_cached(t)
        if cached is None:
            continue
        a = cached["analysis"]
        ids.append(t.take_id)
        blocks.append(
            json.dumps(
                {
                    "take_id": t.take_id,
                    "shot": t.shot,
                    "take_number": t.take_number,
                    "camera": t.camera,
                    "lens_mm": t.lens_mm,
                    "status": t.status,
                    "summary": a["summary"],
                    "transcript": a["transcript"],
                    "actions": a["actions"],
                    "camera_notes": a["camera"],
                },
                indent=1,
            )
        )
    if len(ids) < 2:
        return None
    return ids, "\n\n".join(blocks)


def notes_for_scene(cl, scene: str, live: bool = True) -> list[dict]:
    payload = scene_payload(scene)
    if payload is None:
        return []
    ids, blob = payload
    prompt = PROMPT.format(scene=scene, ids=", ".join(ids), blob=blob)
    key = "cont_" + sha1_text(prompt)
    cached = cache_get(key)
    if cached is not None:
        return cached["notes"]
    if not live:
        return []

    resp, used = generate(
        cl,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ContinuityReport,
            "temperature": 0.4,
        },
    )
    data = json.loads(resp.text)
    ContinuityReport.model_validate(data)
    valid = [
        n
        for n in data["notes"]
        if n["take_id_a"] in ids and n["take_id_b"] in ids and n["take_id_a"] != n["take_id_b"]
    ]
    cache_put(key, {"scene_number": scene, "model": used, "notes": valid})
    return valid


def all_notes(live: bool = True) -> list[tuple[str, dict]]:
    cl = client() if live else None
    out: list[tuple[str, dict]] = []
    for scene in REAL_SCENES:
        for n in notes_for_scene(cl, scene, live=live):
            out.append((scene, n))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="continuity notes for day-12 scenes")
    ap.add_argument("--offline", action="store_true", help="cache only, no API calls")
    args = ap.parse_args()

    rows = all_notes(live=not args.offline)
    for scene, n in rows:
        print(
            f"  {scene:>4}  {n['category']:<14} s{n['severity']}  "
            f"{n['take_id_a']} vs {n['take_id_b']}: {n['description'][:100]}"
        )
    print(f"{len(rows)} continuity notes")
    if not args.offline:
        print(token_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
