"""Editor's Log export — CSV, ALE (Avid Log Exchange) and Markdown.

WHAT THIS IS
------------
The circled-take list an assistant editor carries from the set into the cutting
room. On a real show it is typed by the script supervisor and re-typed by the
assistant editor into Avid; here it falls out of the database that Gemini
already filled in.

**Avid Log Exchange (ALE)** is the interchange format Media Composer has read
since the 1990s: a plain, tab-delimited text file in three sections --

    Heading      key/value pairs (FIELD_DELIM, VIDEO_FORMAT, AUDIO_FORMAT, FPS)
    Column       one tab-delimited row of column names
    Data         one tab-delimited row per clip, in the Column order

Media Composer maps the standard columns straight onto bin columns:
``Name`` (clip name), ``Tracks``, ``Start`` / ``End`` / ``Duration``
(timecode), ``Scene``, ``Take``, ``Camroll``, ``Soundroll``, ``Comments``.
Anything extra becomes a custom bin column, which is where the SlateIQ-specific
columns (Gemini's summary, the QC flags, the quality score) land.

NON-REASONING PATH
------------------
This module is a *reporting/export* path, not an agent path. It reads
ClickHouse through ``clickhouse-connect`` directly, exactly like ``/api/takes``
and ``/api/take/{id}/events``: no LLM is involved, no SQL is generated, the one
statement below is fixed and parameterised. Every *analytical* answer in
SlateIQ still goes through the official ``mcp-clickhouse`` server -- see
``slateiq_agent/agent.py``.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable, Sequence
from typing import Any

from .config import DB

__all__ = [
    "EDITORS_LOG_SQL",
    "FORMATS",
    "ale_columns",
    "editors_log_rows",
    "frames_to_tc",
    "render",
    "tc_to_frames",
    "to_ale",
    "to_csv",
    "to_markdown",
]

FORMATS = ("csv", "ale", "md")

# Fixed, parameterised statement. Circled takes are the point of the document;
# `hold` takes are included when the caller asks for them because an assistant
# editor pulling selects wants the holds in the bin too.
EDITORS_LOG_SQL = f"""
SELECT t.take_id            AS take_id,
       t.day_number         AS day_number,
       t.scene_number       AS scene_number,
       s.slug               AS slug,
       t.shot               AS shot,
       t.take_number        AS take_number,
       t.camera             AS camera,
       t.roll               AS roll,
       t.sound_roll         AS sound_roll,
       t.tc_in              AS tc_in,
       t.duration_s         AS duration_s,
       t.fps                AS fps,
       t.status             AS status,
       t.director_note      AS director_note,
       t.clip_uri           AS clip_uri,
       t.lens_mm            AS lens_mm,
       a.summary            AS summary,
       a.quality_score      AS quality_score,
       f.flags              AS flags
FROM {DB}.take t
LEFT JOIN {DB}.scene s USING (scene_number)
LEFT JOIN {DB}.take_analysis a USING (take_id)
LEFT JOIN (
    SELECT take_id, groupUniqArray(flag_type) AS flags
    FROM {DB}.take_event
    WHERE kind = 'flag' AND flag_type != ''
    GROUP BY take_id
) f USING (take_id)
WHERE t.day_number = %(day)s AND t.status IN %(statuses)s
-- scene_number is a String ('14A' is a real scene), so sort on its
-- numeric head first and fall back to the string for the suffix.
ORDER BY toUInt32OrZero(extract(t.scene_number, '^[0-9]+')),
         t.scene_number, t.shot, t.take_number, t.camera
"""


# ---------------------------------------------------------------------------
# Timecode
# ---------------------------------------------------------------------------
_TC = re.compile(r"^\s*(\d{1,3}):([0-5]?\d):([0-5]?\d)[:;](\d{1,3})\s*$")


def tc_to_frames(tc: str, fps: int = 24) -> int | None:
    """``'12:04:11:00'`` -> absolute frame count. None if it is not a timecode."""
    m = _TC.match(tc or "")
    if not m or fps <= 0:
        return None
    h, mnt, s, f = (int(g) for g in m.groups())
    return ((h * 60 + mnt) * 60 + s) * fps + min(f, fps - 1)


def frames_to_tc(frames: int, fps: int = 24) -> str:
    """Absolute frame count -> ``HH:MM:SS:FF`` (24h wrap, non-drop)."""
    if fps <= 0:
        fps = 24
    frames = max(0, int(frames)) % (24 * 60 * 60 * fps)
    f = frames % fps
    total_s = frames // fps
    return f"{total_s // 3600:02d}:{total_s // 60 % 60:02d}:{total_s % 60:02d}:{f:02d}"


def _fps(row: dict[str, Any]) -> int:
    try:
        return int(row.get("fps") or 24) or 24
    except (TypeError, ValueError):
        return 24


def tc_out(row: dict[str, Any]) -> str:
    """Timecode of the first frame after the take (ALE's exclusive ``End``)."""
    fps = _fps(row)
    start = tc_to_frames(str(row.get("tc_in") or ""), fps)
    if start is None:
        return ""
    return frames_to_tc(start + _duration_frames(row), fps)


def _duration_frames(row: dict[str, Any]) -> int:
    fps = _fps(row)
    try:
        return max(1, round(float(row.get("duration_s") or 0) * fps))
    except (TypeError, ValueError):
        return 1


def duration_tc(row: dict[str, Any]) -> str:
    return frames_to_tc(_duration_frames(row), _fps(row))


def _slate(row: dict[str, Any]) -> str:
    """``12/B/2`` — how a take is spoken about on set and in the cutting room."""
    return f"{row.get('scene_number', '')}/{row.get('shot', '')}/{row.get('take_number', '')}"


def _clip_name(row: dict[str, Any]) -> str:
    """Avid clip name: the slate plus the camera letter (a 2-cam setup is 2 clips)."""
    cam = str(row.get("camera") or "").strip()
    return f"{_slate(row)}{('-' + cam) if cam else ''}"


def _flags(row: dict[str, Any]) -> str:
    flags = row.get("flags") or []
    if isinstance(flags, str):
        flags = [flags]
    return ", ".join(str(f).replace("_", " ") for f in flags if f)


def _quality(row: dict[str, Any]) -> str:
    q = row.get("quality_score")
    if q is None:
        return ""
    try:
        return f"{float(q):.2f}"
    except (TypeError, ValueError):
        return ""


def _clean(value: Any) -> str:
    """One-line, delimiter-safe text. ALE is tab-delimited and line-oriented."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------
def editors_log_rows(
    client: Any, day: int, statuses: Sequence[str] = ("circled",)
) -> list[dict[str, Any]]:
    """Run the fixed export query and return plain dict rows."""
    res = client.query(
        EDITORS_LOG_SQL,
        parameters={"day": int(day), "statuses": tuple(statuses) or ("circled",)},
    )
    rows = [dict(zip(res.column_names, r)) for r in res.result_rows]
    for r in rows:
        r["flags"] = list(r.get("flags") or [])
    return rows


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
CSV_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Scene", "scene_number"),
    ("Slug", "slug"),
    ("Shot", "shot"),
    ("Take", "take_number"),
    ("Camera", "camera"),
    ("Camroll", "roll"),
    ("Soundroll", "sound_roll"),
    ("TC In", "tc_in"),
    ("TC Out", None),
    ("Duration (s)", "duration_s"),
    ("Status", "status"),
    ("Director note", "director_note"),
    ("Gemini summary", "summary"),
    ("Quality", None),
    ("Flags", None),
    ("Take ID", "take_id"),
    ("Clip", "clip_uri"),
)


def _csv_value(header: str, key: str | None, row: dict[str, Any]) -> str:
    if header == "TC Out":
        return tc_out(row)
    if header == "Quality":
        return _quality(row)
    if header == "Flags":
        return _flags(row)
    if header == "Duration (s)":
        try:
            return f"{float(row.get('duration_s') or 0):.2f}"
        except (TypeError, ValueError):
            return ""
    return _clean(row.get(key or ""))


def to_csv(rows: Iterable[dict[str, Any]]) -> str:
    """Spreadsheet form of the log — one row per circled camera slate."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow([h for h, _ in CSV_COLUMNS])
    for row in rows:
        w.writerow([_csv_value(h, k, row) for h, k in CSV_COLUMNS])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# ALE (Avid Log Exchange)
# ---------------------------------------------------------------------------
# The nine standard bin columns Media Composer maps automatically, then the
# SlateIQ-specific ones, which arrive as custom columns.
ALE_STANDARD = (
    "Name",
    "Tracks",
    "Start",
    "End",
    "Duration",
    "Scene",
    "Take",
    "Camroll",
    "Soundroll",
    "Comments",
)
ALE_EXTRA = ("Shot", "Camera", "Circled", "Labroll", "Quality", "Flags", "Summary")


def ale_columns() -> tuple[str, ...]:
    return ALE_STANDARD + ALE_EXTRA


def _ale_row(row: dict[str, Any]) -> dict[str, str]:
    note = _clean(row.get("director_note"))
    return {
        "Name": _clip_name(row),
        # Every clip here is picture + 2 channels of production sound.
        "Tracks": "V A1A2",
        "Start": _clean(row.get("tc_in")),
        "End": tc_out(row),
        "Duration": duration_tc(row),
        "Scene": _clean(row.get("scene_number")),
        "Take": _clean(row.get("take_number")),
        "Camroll": _clean(row.get("roll")),
        "Soundroll": _clean(row.get("sound_roll")),
        # Comments is the column an editor actually reads in the bin, so it
        # carries the director's note first and Gemini's description after it.
        "Comments": note or _clean(row.get("summary")),
        "Shot": _clean(row.get("shot")),
        "Camera": _clean(row.get("camera")),
        # Avid's own convention for the circled-take column.
        "Circled": "KEEP" if str(row.get("status") or "").lower() == "circled" else "",
        "Labroll": _clean(row.get("roll")),
        "Quality": _quality(row),
        "Flags": _flags(row),
        "Summary": _clean(row.get("summary")),
    }


def to_ale(
    rows: Iterable[dict[str, Any]],
    *,
    fps: int = 24,
    video_format: str = "1080",
    audio_format: str = "48khz",
) -> str:
    """Render an Avid Log Exchange file (tab-delimited, CRLF, 3 sections)."""
    rows = list(rows)
    if rows:
        fps = _fps(rows[0])
    cols = ale_columns()
    out: list[str] = [
        "Heading",
        "FIELD_DELIM\tTABS",
        f"VIDEO_FORMAT\t{video_format}",
        f"AUDIO_FORMAT\t{audio_format}",
        f"FPS\t{fps}",
        "",
        "Column",
        "\t".join(cols),
        "",
        "Data",
    ]
    for row in rows:
        rendered = _ale_row(row)
        # A tab or newline inside a value would break the column alignment.
        out.append("\t".join(_clean(rendered.get(c, "")) for c in cols))
    out.append("")
    return "\r\n".join(out)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def to_markdown(rows: Iterable[dict[str, Any]], day: int) -> str:
    """The same log as the paper version: grouped by scene, circled takes only."""
    rows = list(rows)
    lines = [
        f"# EDITOR'S LOG — Day {day}",
        "",
        f"Circled takes: **{len(rows)}** across "
        f"**{len({str(r.get('scene_number')) for r in rows})}** scenes. "
        "Exported straight from the take index (ClickHouse); "
        "ALE and CSV of the same rows are available from Production Health.",
        "",
    ]
    if not rows:
        lines.append(f"_No circled takes logged on day {day}._")
        return "\n".join(lines) + "\n"

    scenes: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        scenes.setdefault(str(r.get("scene_number") or "?"), []).append(r)

    for scene, takes in scenes.items():
        slug = _clean(takes[0].get("slug"))
        lines += [
            f"## Scene {scene}" + (f" — {slug}" if slug else ""),
            "",
            "| Shot | Take | Cam | TC In | Dur | Camroll | Note | Flags |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for t in takes:
            dur = f"{float(t.get('duration_s') or 0):.1f}s"
            lines.append(
                f"| {_clean(t.get('shot'))} | {_clean(t.get('take_number'))} "
                f"| {_clean(t.get('camera'))} | {_clean(t.get('tc_in'))} | {dur} "
                f"| {_clean(t.get('roll'))} | {_clean(t.get('director_note')) or '—'} "
                f"| {_flags(t) or '—'} |"
            )
        lines.append("")
        for t in takes:
            summary = _clean(t.get("summary"))
            if summary:
                lines.append(f"- **{_slate(t)}** — {summary}")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def render(rows: Iterable[dict[str, Any]], fmt: str, day: int) -> tuple[str, str, str]:
    """``(body, media_type, filename)`` for one of ``csv`` / ``ale`` / ``md``."""
    fmt = (fmt or "csv").lower().strip()
    stem = f"slateiq_editors_log_day{int(day):02d}"
    if fmt == "ale":
        return to_ale(rows), "text/plain; charset=utf-8", f"{stem}.ale"
    if fmt in ("md", "markdown"):
        return to_markdown(rows, day), "text/markdown; charset=utf-8", f"{stem}.md"
    if fmt == "csv":
        return to_csv(rows), "text/csv; charset=utf-8", f"{stem}.csv"
    raise ValueError(f"unknown format '{fmt}' -- use one of {', '.join(FORMATS)}")
