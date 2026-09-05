"""On-disk cache for the two generated documents (DPR / Editor's Log).

A finished shooting day does not change, and a full Daily Progress Report is
10-13 `run_query` round trips and ~90 seconds. `/api/report/dpr` has always
cached the result here; this module is that cache lifted out of `main.py` so
the **report agent** can read the very same files from a chat turn
(`get_cached_report`) instead of rebuilding a document that is already on disk.

Nothing here touches ClickHouse: it is a local file read, which is why the
trace labels it as a plain function tool and never as an MCP call. The MCP
path stays the only way any *data* reaches the agent -- the cached markdown was
itself produced by `run_query` calls through `mcp-clickhouse`, and the prompt
requires the answer to keep saying so.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "CACHED_REPORT_MARKER",
    "KIND_ALIASES",
    "cache_path",
    "get_cached_report",
    "normalise_kind",
    "read_report",
    "save_cached_report",
    "write_report",
]

_REPO_ROOT = Path(__file__).resolve().parents[2]

# A cached DPR is ~10 000 characters; making the model retype it costs ~20 s of
# output tokens for a document already on disk. The report agent emits this
# marker instead and `runtime.stream_agent` splices the cached markdown in.
CACHED_REPORT_MARKER = "[[SLATEIQ_CACHED_REPORT]]"

# The chat-facing names ("editors_log", the way an editor says it) mapped onto
# the file names `/api/report/*` has been writing since sprint 2.
KIND_ALIASES = {
    "dpr": "dpr",
    "daily_progress_report": "dpr",
    "daily-progress-report": "dpr",
    "report": "dpr",
    "editor_log": "editor_log",
    "editors_log": "editor_log",
    "editor's_log": "editor_log",
    "editors-log": "editor_log",
    "editor-log": "editor_log",
    "log": "editor_log",
}


def cache_dir() -> Path:
    """Read the env var on every call so tests can point it at a tmpdir."""
    return Path(
        os.environ.get("SLATEIQ_REPORT_CACHE", str(_REPO_ROOT / "data" / "cache" / "reports"))
    )


def normalise_kind(kind: str) -> str | None:
    return KIND_ALIASES.get((kind or "").strip().lower().replace(" ", "_"))


def cache_path(kind: str, day: int) -> Path:
    return cache_dir() / f"{kind}_day{int(day):02d}.json"


def read_report(kind: str, day: int) -> dict[str, Any] | None:
    try:
        return json.loads(cache_path(kind, day).read_text("utf-8"))
    except Exception:
        return None


def write_report(kind: str, day: int, payload: dict[str, Any]) -> None:
    try:
        path = cache_path(kind, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=1, default=str), "utf-8")
    except Exception as exc:  # caching is best-effort
        logger.warning("could not cache %s day %s: %s", kind, day, exc)


def get_cached_report(kind: str, day: int) -> dict[str, Any]:
    """Look up an already-generated report for one shooting day.

    Args:
        kind: `dpr` for the Daily Progress Report, `editors_log` for the
            Editor's Log.
        day: shooting day number, e.g. 12.

    Returns:
        `{"found": true, "kind":..., "day":..., "generated_at":...,
        "queries": n, "markdown": "..."}` when the document is already on
        disk, otherwise `{"found": false, "reason": "..."}` -- in which case
        generate the report from live queries as usual.
    """
    key = normalise_kind(kind)
    if key is None:
        return {
            "found": False,
            "reason": f"unknown report kind {kind!r} -- use 'dpr' or 'editors_log'",
        }
    try:
        day_n = int(day)
    except (TypeError, ValueError):
        return {"found": False, "reason": f"day must be a number, got {day!r}"}
    if not 1 <= day_n <= 365:
        return {"found": False, "reason": f"day {day_n} is out of range"}

    payload = read_report(key, day_n)
    markdown = (payload or {}).get("markdown") or ""
    if not markdown.strip():
        return {
            "found": False,
            "kind": key,
            "day": day_n,
            "reason": (
                f"no cached {key} for day {day_n} -- generate it from live "
                "queries through mcp-clickhouse"
            ),
        }
    path = cache_path(key, day_n)
    try:
        generated_at = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.UTC).isoformat(
            timespec="seconds"
        )
    except Exception:  # pragma: no cover - stat should not fail after a read
        generated_at = ""
    return {
        "found": True,
        "kind": key,
        "day": day_n,
        "generated_at": payload.get("generated_at") or generated_at,
        "queries": payload.get("tool_calls"),
        "source": "SlateIQ report cache (built earlier from ClickHouse via mcp-clickhouse)",
        "markdown": markdown,
    }


def save_cached_report(kind: str, day: int, markdown: str, **extra: Any) -> bool:
    """Persist a freshly generated report so the next request is instant."""
    key = normalise_kind(kind)
    if key is None or not (markdown or "").strip():
        return False
    try:
        day_n = int(day)
    except (TypeError, ValueError):
        return False
    payload = {
        "day": day_n,
        "markdown": markdown,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "cached": False,
        **extra,
    }
    payload.setdefault("sql", [])
    write_report(key, day_n, payload)
    return True
