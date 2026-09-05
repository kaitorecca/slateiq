"""Unit tests for the Editor's Log export (CSV / ALE / Markdown).

The ALE half is the part that has to be exactly right: Media Composer parses
the file positionally, so a missing section header, a re-ordered column or a
stray tab inside a value silently corrupts a bin. Everything here runs against
fabricated rows -- no ClickHouse, no MCP, no model.
"""

from __future__ import annotations

import csv
import io

import pytest
from slateiq_agent import export
from slateiq_agent.export import (
    ale_columns,
    frames_to_tc,
    render,
    tc_to_frames,
    to_ale,
    to_csv,
    to_markdown,
)

FPS = 24


def row(**over):
    base = dict(
        take_id="TOS-D12-S12-B-02-B",
        day_number=12,
        scene_number="12",
        slug="INT. LAB - NIGHT",
        shot="B",
        take_number=2,
        camera="B",
        roll="B012",
        sound_roll="S012",
        tc_in="12:26:18:20",
        duration_s=16.2,
        fps=FPS,
        status="circled",
        director_note="Cleaner. Print.",
        clip_uri="clips/TOS-D12-S12-B-02-B.mp4",
        lens_mm=50,
        summary="An older man rests on a cot while a soldier keeps watch.",
        quality_score=0.9,
        flags=["soft_focus"],
    )
    base.update(over)
    return base


ROWS = [
    row(),
    row(
        take_id="TOS-D12-S102-A-01-A",
        scene_number="102",
        shot="A",
        take_number=1,
        camera="A",
        tc_in="19:06:30:11",
        duration_s=13.667,
        flags=[],
        director_note="Final of the day — got it.",
    ),
]


# ---------------------------------------------------------------------------
# Timecode
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tc, frames",
    [
        ("00:00:00:00", 0),
        ("00:00:01:00", 24),
        ("00:00:01:12", 36),
        ("01:00:00:00", 24 * 3600),
        ("12:26:18:20", ((12 * 60 + 26) * 60 + 18) * 24 + 20),
    ],
)
def test_timecode_round_trips(tc: str, frames: int) -> None:
    assert tc_to_frames(tc, FPS) == frames
    assert frames_to_tc(frames, FPS) == tc


def test_drop_frame_separator_is_accepted() -> None:
    assert tc_to_frames("00:00:01;00", 24) == 24


def test_a_non_timecode_is_not_guessed_at() -> None:
    for bad in ("", "not a timecode", "12:26:18", "12-26-18-20"):
        assert tc_to_frames(bad, FPS) is None


def test_a_frame_number_past_the_rate_is_clamped_not_wrapped() -> None:
    # A malformed ':30' at 24 fps must not silently become the next second.
    assert tc_to_frames("00:00:00:30", 24) == 23


def test_timecode_wraps_at_24_hours() -> None:
    assert frames_to_tc(24 * 3600 * FPS, FPS) == "00:00:00:00"


def test_end_is_start_plus_duration() -> None:
    r = row(tc_in="12:26:18:20", duration_s=16.2, fps=FPS)
    assert export.tc_out(r) == frames_to_tc(
        tc_to_frames("12:26:18:20", FPS) + round(16.2 * FPS), FPS
    )
    assert export.duration_tc(r) == "00:00:16:05"


def test_a_missing_start_timecode_leaves_end_empty_rather_than_wrong() -> None:
    assert export.tc_out(row(tc_in="")) == ""


def test_a_sub_frame_take_still_has_one_frame_of_duration() -> None:
    assert export.duration_tc(row(duration_s=0.0)) == "00:00:00:01"


# ---------------------------------------------------------------------------
# ALE
# ---------------------------------------------------------------------------
def parse_ale(text: str) -> tuple[dict[str, str], list[str], list[list[str]]]:
    """Parse an ALE the way Media Composer does: by section, positionally."""
    lines = text.split("\r\n")
    assert lines[0] == "Heading", "an ALE must open with the Heading section"
    i = 1
    heading: dict[str, str] = {}
    while lines[i]:
        k, _, v = lines[i].partition("\t")
        heading[k] = v
        i += 1
    assert lines[i + 1] == "Column"
    columns = lines[i + 2].split("\t")
    assert lines[i + 3] == ""
    assert lines[i + 4] == "Data"
    data = [ln.split("\t") for ln in lines[i + 5 :] if ln]
    return heading, columns, data


def test_ale_has_the_three_sections_in_order() -> None:
    heading, columns, data = parse_ale(to_ale(ROWS))
    assert heading["FIELD_DELIM"] == "TABS"
    assert heading["FPS"] == str(FPS)
    assert "VIDEO_FORMAT" in heading and "AUDIO_FORMAT" in heading
    assert columns[:10] == list(
        (
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
    )
    assert len(data) == len(ROWS)


def test_ale_is_crlf_terminated() -> None:
    text = to_ale(ROWS)
    assert "\r\n" in text
    assert "\n" not in text.replace("\r\n", "")


def test_every_data_row_has_exactly_as_many_fields_as_there_are_columns() -> None:
    _, columns, data = parse_ale(to_ale(ROWS))
    assert all(len(r) == len(columns) for r in data)


def test_ale_carries_the_slate_the_rolls_and_the_note() -> None:
    _, columns, data = parse_ale(to_ale([row()]))
    rec = dict(zip(columns, data[0]))
    assert rec["Name"] == "12/B/2-B"  # slate + camera letter
    assert rec["Scene"] == "12"
    assert rec["Take"] == "2"
    assert rec["Camroll"] == "B012"
    assert rec["Soundroll"] == "S012"
    assert rec["Start"] == "12:26:18:20"
    assert rec["Comments"] == "Cleaner. Print."
    assert rec["Circled"] == "KEEP"
    assert rec["Flags"] == "soft focus"
    assert rec["Tracks"] == "V A1A2"


def test_gemini_summary_fills_comments_when_the_director_said_nothing() -> None:
    _, columns, data = parse_ale(to_ale([row(director_note="")]))
    rec = dict(zip(columns, data[0]))
    assert rec["Comments"].startswith("An older man rests")


def test_a_newline_or_tab_in_a_note_cannot_break_the_columns() -> None:
    nasty = row(director_note="line one\nline\ttwo   ", summary="a\r\nb")
    _, columns, data = parse_ale(to_ale([nasty]))
    assert len(data) == 1 and len(data[0]) == len(columns)
    assert dict(zip(columns, data[0]))["Comments"] == "line one line two"


def test_an_empty_day_still_produces_a_valid_ale() -> None:
    heading, columns, data = parse_ale(to_ale([]))
    assert data == []
    assert columns == list(ale_columns())
    assert heading["FPS"] == "24"


def test_the_fps_header_follows_the_footage_not_the_default() -> None:
    heading, _, _ = parse_ale(to_ale([row(fps=25)]))
    assert heading["FPS"] == "25"


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def test_csv_has_a_header_and_one_row_per_take() -> None:
    parsed = list(csv.reader(io.StringIO(to_csv(ROWS))))
    assert parsed[0][0] == "Scene"
    assert len(parsed) == len(ROWS) + 1


def test_csv_carries_the_columns_an_assistant_editor_asked_for() -> None:
    parsed = list(csv.DictReader(io.StringIO(to_csv([row()]))))
    rec = parsed[0]
    assert rec["Scene"] == "12"
    assert rec["Shot"] == "B"
    assert rec["Take"] == "2"
    assert rec["Camera"] == "B"
    assert rec["Camroll"] == "B012"
    assert rec["Soundroll"] == "S012"
    assert rec["TC In"] == "12:26:18:20"
    assert rec["Duration (s)"] == "16.20"
    assert rec["Director note"] == "Cleaner. Print."
    assert rec["Gemini summary"].startswith("An older man")
    assert rec["Flags"] == "soft focus"
    assert rec["Take ID"] == "TOS-D12-S12-B-02-B"


def test_a_comma_in_a_note_is_quoted_not_split() -> None:
    parsed = list(csv.DictReader(io.StringIO(to_csv([row(director_note="soft, but her eyes")]))))
    assert parsed[0]["Director note"] == "soft, but her eyes"


def test_missing_analysis_columns_render_as_empty_not_none() -> None:
    parsed = list(
        csv.DictReader(io.StringIO(to_csv([row(summary=None, quality_score=None, flags=None)])))
    )
    assert parsed[0]["Gemini summary"] == ""
    assert parsed[0]["Quality"] == ""
    assert parsed[0]["Flags"] == ""


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def test_markdown_groups_by_scene_and_counts_the_circled_takes() -> None:
    md = to_markdown(ROWS, 12)
    assert md.startswith("# EDITOR'S LOG — Day 12")
    assert "**2**" in md  # two circled takes
    assert "## Scene 12 — INT. LAB - NIGHT" in md
    assert "## Scene 102" in md


def test_markdown_says_so_plainly_when_nothing_was_circled() -> None:
    md = to_markdown([], 20)
    assert "No circled takes" in md


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "fmt, media_type, suffix",
    [
        ("csv", "text/csv", ".csv"),
        ("ale", "text/plain", ".ale"),
        ("md", "text/markdown", ".md"),
        ("ALE", "text/plain", ".ale"),
    ],
)
def test_render_dispatch(fmt: str, media_type: str, suffix: str) -> None:
    body, mt, filename = render(ROWS, fmt, 12)
    assert body
    assert mt.startswith(media_type)
    assert filename.endswith(suffix)
    assert "day12" in filename


def test_an_unknown_format_is_refused_rather_than_guessed() -> None:
    with pytest.raises(ValueError):
        render(ROWS, "xml", 12)


# ---------------------------------------------------------------------------
# The query itself (text only -- it is fixed and parameterised on purpose)
# ---------------------------------------------------------------------------
def test_the_export_query_is_a_single_parameterised_select() -> None:
    sql = export.EDITORS_LOG_SQL.strip()
    assert sql.upper().startswith("SELECT")
    assert sql.count(";") == 0
    # Day and status are bound, never interpolated -- this path takes user input
    # straight from a query string.
    assert "%(day)s" in sql and "%(statuses)s" in sql


def test_the_export_query_passes_the_agent_guardrail_too() -> None:
    """Belt and braces: the export SQL is read-only by the same standard."""
    from slateiq_agent.guardrails import enforce

    probe = export.EDITORS_LOG_SQL.replace("%(day)s", "12").replace("%(statuses)s", "('circled')")
    assert enforce(probe)[0] is None


def test_rows_are_ordered_by_scene_number_numerically() -> None:
    # scene_number is a String, so '102' must not sort before '12'.
    assert "toUInt32OrZero" in export.EDITORS_LOG_SQL
