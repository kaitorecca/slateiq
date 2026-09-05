"""Unit tests for the report cache and the `get_cached_report` function tool.

QC #4 issue #4: the DPR button reads this cache in 0.5 s while the same request
in chat rebuilt the document in 87 s. These cover the tool the report agent now
calls first -- no ClickHouse, no MCP, no model.
"""

from __future__ import annotations

import json

import pytest
from slateiq_agent import report_cache


@pytest.fixture(autouse=True)
def _tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("SLATEIQ_REPORT_CACHE", str(tmp_path))
    return tmp_path


def _write(tmp_path, name: str, markdown: str, **extra) -> None:
    (tmp_path / name).write_text(
        json.dumps({"day": 12, "markdown": markdown, **extra}), encoding="utf-8"
    )


def test_hit_returns_the_markdown_the_http_endpoint_wrote(_tmp_cache):
    # exactly the file `/api/report/dpr` writes, including its 2-digit day
    _write(_tmp_cache, "dpr_day12.json", "# DAILY PROGRESS REPORT\n| Scene |\n", tool_calls=13)

    got = report_cache.get_cached_report("dpr", 12)

    assert got["found"] is True
    assert got["markdown"].startswith("# DAILY PROGRESS REPORT")
    assert got["day"] == 12 and got["kind"] == "dpr"
    assert got["generated_at"]  # falls back to the file mtime
    assert "mcp-clickhouse" in got["source"]


def test_miss_tells_the_model_to_generate_it(_tmp_cache):
    got = report_cache.get_cached_report("dpr", 7)

    assert got["found"] is False
    assert "mcp-clickhouse" in got["reason"]
    assert "markdown" not in got


@pytest.mark.parametrize(
    ("asked", "filename"),
    [
        ("editors_log", "editor_log_day12.json"),
        ("editor's log", "editor_log_day12.json"),
        ("DPR", "dpr_day12.json"),
    ],
)
def test_chat_spellings_map_onto_the_endpoint_filenames(_tmp_cache, asked, filename):
    _write(_tmp_cache, filename, "# LOG\n| Shot |\n")

    assert report_cache.get_cached_report(asked, 12)["found"] is True


def test_bad_input_is_a_clean_miss_not_a_crash(_tmp_cache):
    assert report_cache.get_cached_report("weather_report", 12)["found"] is False
    assert report_cache.get_cached_report("dpr", 999)["found"] is False
    assert report_cache.get_cached_report("dpr", "twelve")["found"] is False
    # an empty document on disk is a miss, not a hit with a blank report
    _write(_tmp_cache, "dpr_day03.json", "   ")
    assert report_cache.get_cached_report("dpr", 3)["found"] is False


class _Part:
    def __init__(self, text=None, function_call=None):
        self.text = text
        self.function_call = function_call


class _Content:
    def __init__(self, parts):
        self.parts = parts


class _Resp:
    def __init__(self, parts, partial=False):
        self.content = _Content(parts)
        self.partial = partial


class _Ctx:
    def __init__(self, state):
        self.state = state


def test_fresh_report_is_written_back_to_the_same_cache(_tmp_cache):
    """The agent never re-emits the markdown: the callback caches the answer."""
    from slateiq_agent.agent import REPORT_REQUEST_KEY, _cache_fresh_report

    state = {REPORT_REQUEST_KEY: {"kind": "dpr", "day": 4, "found": False}}
    report = "# DAILY PROGRESS REPORT\n" + "| Scene | Pages |\n" * 60

    assert _cache_fresh_report(_Ctx(state), _Resp([_Part(text=report)])) is None
    assert report_cache.get_cached_report("dpr", 4)["found"] is True
    assert state[REPORT_REQUEST_KEY]["found"] is True


def test_the_callback_never_caches_chatter_or_a_cache_hit(_tmp_cache):
    from slateiq_agent.agent import REPORT_REQUEST_KEY, _cache_fresh_report

    miss = {REPORT_REQUEST_KEY: {"kind": "dpr", "day": 5, "found": False}}
    # a short clarifying question is not a report
    _cache_fresh_report(_Ctx(miss), _Resp([_Part(text="Which shooting day?")]))
    # neither is a partial stream chunk, nor a turn that is calling a tool
    _cache_fresh_report(_Ctx(miss), _Resp([_Part(text="# DPR\n| x |\n" * 80)], partial=True))
    _cache_fresh_report(_Ctx(miss), _Resp([_Part(function_call=object())]))
    assert report_cache.get_cached_report("dpr", 5)["found"] is False

    # an answer that is the cached document itself must not rewrite the file
    hit = {REPORT_REQUEST_KEY: {"kind": "dpr", "day": 6, "found": True}}
    marker = report_cache.CACHED_REPORT_MARKER
    _cache_fresh_report(_Ctx(hit), _Resp([_Part(text=f"{marker}\n| x |\n" * 80)]))
    assert report_cache.get_cached_report("dpr", 6)["found"] is False
    # no report request on state at all -> nothing is cached
    _cache_fresh_report(_Ctx({}), _Resp([_Part(text="# DPR\n| x |\n" * 80)]))


def test_a_refresh_overwrites_the_cached_copy(_tmp_cache):
    """ "Refresh the DPR" regenerates -- and the new document replaces the old."""
    from slateiq_agent.agent import REPORT_REQUEST_KEY, _cache_fresh_report

    _write(_tmp_cache, "dpr_day12.json", "# OLD REPORT\n| a |\n")
    # the agent looked the cache up (a hit), then the user asked to refresh
    state = {REPORT_REQUEST_KEY: {"kind": "dpr", "day": 12, "found": True}}
    fresh = "# DAILY PROGRESS REPORT\n" + "| Scene | Pages |\n" * 60

    _cache_fresh_report(_Ctx(state), _Resp([_Part(text=fresh)]))

    assert report_cache.get_cached_report("dpr", 12)["markdown"].startswith(
        "# DAILY PROGRESS REPORT"
    )


def test_save_round_trips_and_stamps_the_time(_tmp_cache):
    assert report_cache.save_cached_report("editors_log", 9, "# LOG\n| a |\n") is True

    got = report_cache.get_cached_report("editors_log", 9)
    assert got["found"] is True
    assert got["markdown"].startswith("# LOG")
    assert got["generated_at"].endswith("+00:00")
    # an empty report is never written
    assert report_cache.save_cached_report("dpr", 9, "  ") is False
    assert report_cache.get_cached_report("dpr", 9)["found"] is False
