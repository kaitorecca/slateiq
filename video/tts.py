#!/usr/bin/env python3
"""Generate one VO clip per beat with Gemini TTS.

    set -a; source .env; set +a
    .venv/bin/python video/tts.py

Writes data/video/vo/<id>.wav (24 kHz mono PCM) and prints the duration of each.
Results are cached: a beat is only re-synthesised when its text changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "video" / "vo.json").read_text())
OUT = ROOT / "data" / "video" / "vo"
OUT.mkdir(parents=True, exist_ok=True)

RATE = 24_000


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)


def _synth(client, spec, text, attempts: int = 8) -> bytes:
    """Gemini TTS 500s and occasionally returns an empty candidate — retry both."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            resp = client.models.generate_content(
                model=spec["model"],
                contents=f'{spec["style"]}\n\n{text}',
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=spec["voice"])
                        )
                    ),
                ),
            )
            part = resp.candidates[0].content.parts[0]  # type: ignore[union-attr]
            data = part.inline_data.data  # type: ignore[union-attr]
            if not data:
                raise RuntimeError("empty audio part")
            return data
        except Exception as e:  # noqa: BLE001 — transport, server and empty-candidate failures are all retryable
            last = e
            print(f"  retry {i + 1}/{attempts}: {type(e).__name__}: {e}"[:160], file=sys.stderr)
            time.sleep(3 * (i + 1))
    raise last  # type: ignore[misc]


def main() -> int:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("GEMINI_API_KEY / GOOGLE_API_KEY not set", file=sys.stderr)
        return 1
    client = genai.Client(api_key=key)

    manifest: dict[str, dict] = {}
    mpath = OUT / "manifest.json"
    if mpath.exists():
        manifest = json.loads(mpath.read_text())

    total = 0.0
    for beat in SPEC["beats"]:
        bid, text = beat["id"], beat["text"]
        wav = OUT / f"{bid}.wav"
        digest = hashlib.sha256(f'{SPEC["voice"]}|{SPEC["style"]}|{text}'.encode()).hexdigest()[:16]

        if wav.exists() and manifest.get(bid, {}).get("sha") == digest:
            pass  # cached — Gemini calls are not free, never re-spend on identical text
        else:
            write_wav(wav, _synth(client, SPEC, text))

        with wave.open(str(wav), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        manifest[bid] = {"sha": digest, "dur": round(dur, 3), "text": text}
        total += dur
        print(f"{bid}  {dur:6.2f}s  {text[:64]}…")

    mpath.write_text(json.dumps(manifest, indent=2))
    print(f"\nTOTAL VO {total:.1f}s ({int(total // 60)}:{total % 60:04.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
