"""Thin Gemini helper: client, retry/backoff, token accounting, disk cache.

Only Google AI is used in SlateIQ product code (see CLAUDE.md).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

from config import CACHE_DIR, GEMINI_FALLBACK_MODEL, GEMINI_MODEL

_TOKENS = {"prompt": 0, "output": 0, "total": 0, "calls": 0}


def client():
    from google import genai

    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GOOGLE_API_KEY / GEMINI_API_KEY not set (set -a; source .env; set +a)")
    return genai.Client(api_key=key)


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def cache_get(key: str) -> dict | None:
    p = cache_path(key)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None
    return None


def cache_put(key: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path(key).write_text(json.dumps(payload, indent=2, sort_keys=True))


def _account(resp) -> None:
    um = getattr(resp, "usage_metadata", None)
    if not um:
        return
    _TOKENS["prompt"] += getattr(um, "prompt_token_count", 0) or 0
    _TOKENS["output"] += getattr(um, "candidates_token_count", 0) or 0
    _TOKENS["total"] += getattr(um, "total_token_count", 0) or 0
    _TOKENS["calls"] += 1


def token_report() -> str:
    t = _TOKENS
    return (
        f"gemini: {t['calls']} live call(s), prompt={t['prompt']} "
        f"output={t['output']} total={t['total']} tokens"
    )


def generate(cl, *, contents, config, model: str | None = None, attempts: int = 5):
    """generate_content with 429/5xx backoff and a model fallback."""
    models = [model or GEMINI_MODEL, GEMINI_FALLBACK_MODEL]
    last: Exception | None = None
    for m in models:
        for i in range(attempts):
            try:
                resp = cl.models.generate_content(model=m, contents=contents, config=config)
                _account(resp)
                return resp, m
            except Exception as exc:
                last = exc
                msg = str(exc)
                retryable = any(
                    s in msg
                    for s in ("429", "RESOURCE_EXHAUSTED", "503", "500", "UNAVAILABLE", "deadline")
                )
                if not retryable:
                    break  # try the fallback model
                wait = min(60.0, (2**i) * 2.0) + random.random() * 1.5
                print(f"    retry in {wait:.1f}s ({msg[:90]})", file=sys.stderr)
                time.sleep(wait)
        print(f"    model {m} failed, falling back", file=sys.stderr)
    raise RuntimeError(f"gemini call failed: {last}")


def upload_active(cl, path: Path, timeout: float = 300.0):
    """Upload a media file and block until the File API reports ACTIVE."""
    f = cl.files.upload(file=str(path))
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = getattr(f.state, "name", str(f.state))
        if state == "ACTIVE":
            return f
        if state == "FAILED":
            raise RuntimeError(f"file upload failed for {path.name}")
        time.sleep(2.0)
        f = cl.files.get(name=f.name)
    raise TimeoutError(f"file {path.name} never became ACTIVE")
