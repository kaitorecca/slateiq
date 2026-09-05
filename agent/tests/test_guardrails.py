"""Unit tests for the tool-level SQL guardrail.

These are the rules that stand between a chat box and a production database,
so every one of them is pinned here -- including the five holes QC #2 found
(system.* reads, external table functions, unbounded groupArray, LIMIT after
FORMAT, comment stripping inside string literals).

No database, no MCP server and no model are involved: `guardrails.enforce` is
pure text in / text out.
"""

from __future__ import annotations

import pytest
from slateiq_agent import guardrails
from slateiq_agent.config import MAX_ROWS
from slateiq_agent.guardrails import enforce, validate_sql

DB = "slateiq"


def ok(sql: str) -> str:
    """Assert the statement passes and return the SQL that would really run."""
    reason, safe = enforce(sql)
    assert reason is None, f"unexpectedly rejected: {reason}"
    return safe


def rejected(sql: str) -> str:
    reason, _ = enforce(sql)
    assert reason is not None, "expected the guardrail to reject this"
    return reason


# ---------------------------------------------------------------------------
# SELECT-only
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sql",
    [
        f"SELECT count() FROM {DB}.take",
        f"select take_id from {DB}.take limit 5",
        "  \n SELECT 1 ",
        "WITH x AS (SELECT 1 AS a) SELECT a FROM x LIMIT 1",
        # A literal that merely contains a scary word is production data, not a
        # statement -- searching dialogue for "drop" must keep working.
        f"SELECT text FROM {DB}.take_event WHERE text ILIKE '%drop%' LIMIT 10",
        f"SELECT slug FROM {DB}.scene WHERE slug = 'INT. SYSTEM CORE - NIGHT' LIMIT 5",
    ],
)
def test_accepts_read_only_selects(sql: str) -> None:
    ok(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO slateiq.take VALUES (1)",
        "DROP TABLE slateiq.take",
        "TRUNCATE TABLE slateiq.take",
        "ALTER TABLE slateiq.take DELETE WHERE 1=1",
        "CREATE TABLE slateiq.x (a Int)",
        "GRANT SELECT ON *.* TO bob",
        "SYSTEM FLUSH LOGS",
        "KILL QUERY WHERE 1",
        "UPDATE slateiq.take SET status = 'circled'",
        "DELETE FROM slateiq.take",
    ],
)
def test_rejects_writes_and_ddl(sql: str) -> None:
    rejected(sql)


def test_rejects_empty_query() -> None:
    assert enforce("")[0] == "empty query"
    assert enforce("   ")[0] == "empty query"


def test_rejects_multiple_statements() -> None:
    reason = rejected("SELECT 1; DROP TABLE slateiq.take")
    assert "multiple statements" in reason


def test_semicolon_inside_a_literal_is_not_a_statement_break() -> None:
    ok(f"SELECT text FROM {DB}.take_event WHERE text = 'wait; listen' LIMIT 5")


def test_rejects_a_with_block_with_no_select() -> None:
    rejected("WITH x AS (1)")


def test_rejects_a_destructive_statement_hidden_behind_a_comment() -> None:
    rejected("-- harmless\nDROP TABLE slateiq.take")


# ---------------------------------------------------------------------------
# system.* (QC #2 finding G-1)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM system.query_log LIMIT 10",
        "SELECT name FROM system.users LIMIT 10",
        "SELECT * FROM  system . tables LIMIT 5",
        "SELECT * FROM SYSTEM.settings LIMIT 5",
        "WITH q AS (SELECT query FROM system.query_log LIMIT 5) SELECT * FROM q",
    ],
)
def test_blocks_the_system_database(sql: str) -> None:
    assert "system" in rejected(sql)


def test_a_column_called_system_is_not_the_system_database() -> None:
    # `readonly=1` does not block system.* reads, so this rule is ours -- but
    # it must not swallow ordinary identifiers that merely end in "system".
    ok(f"SELECT ecosystem.scene_number FROM {DB}.take AS ecosystem LIMIT 5")
    ok(f"SELECT text FROM {DB}.take_event WHERE text LIKE '%system.%' LIMIT 5")


# ---------------------------------------------------------------------------
# External table functions (QC #2 finding G-2)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "fn, arg",
    [
        ("url", "'http://169.254.169.254/latest/meta-data/', CSV"),
        ("file", "'/etc/passwd', CSV"),
        ("remote", "'127.0.0.1:9000', system.one"),
        ("s3", "'https://x/y.csv', CSV"),
        ("mysql", "'h:3306', 'db', 't', 'u', 'p'"),
        ("postgresql", "'h:5432', 'db', 't', 'u', 'p'"),
        ("executable", "'script.sh', TabSeparated"),
        ("hdfs", "'hdfs://x/y', CSV"),
    ],
)
def test_blocks_external_table_functions(fn: str, arg: str) -> None:
    reason = rejected(f"SELECT * FROM {fn}({arg}) LIMIT 5")
    assert fn.lower() in reason.lower() or "system" in reason


def test_blocks_a_table_function_with_whitespace_before_the_paren() -> None:
    rejected("SELECT * FROM url ('http://evil/', CSV) LIMIT 1")


def test_rejects_file_output() -> None:
    assert "file output" in rejected(f"SELECT * FROM {DB}.take INTO OUTFILE '/tmp/x.csv'")
    assert "file output" in rejected(f"SELECT * FROM {DB}.take FORMAT CSVFile")


# ---------------------------------------------------------------------------
# LIMIT: appended when missing, clamped when oversized
# ---------------------------------------------------------------------------
def test_appends_a_missing_limit() -> None:
    assert ok(f"SELECT take_id FROM {DB}.take") == (
        f"SELECT take_id FROM {DB}.take LIMIT {MAX_ROWS}"
    )


def test_clamps_an_oversized_limit() -> None:
    safe = ok(f"SELECT take_id FROM {DB}.take LIMIT 100000")
    assert safe.endswith(f"LIMIT {MAX_ROWS}")
    assert "100000" not in safe


def test_keeps_a_small_limit_untouched() -> None:
    sql = f"SELECT take_id FROM {DB}.take LIMIT 10"
    assert ok(sql) == sql


def test_a_bare_aggregate_needs_no_limit() -> None:
    # `SELECT 1` / `SELECT now()` have no FROM, so there is nothing to bound.
    assert ok("SELECT 1") == "SELECT 1"


def test_a_subquery_limit_does_not_count_as_the_outer_bound() -> None:
    safe = ok(f"SELECT s.scene_number FROM (SELECT scene_number FROM {DB}.take LIMIT 5) AS s")
    assert safe.endswith(f"LIMIT {MAX_ROWS}")
    assert "LIMIT 5" in safe  # the inner one survives


def test_limit_is_appended_before_a_settings_clause() -> None:
    safe = ok(f"SELECT * FROM {DB}.take SETTINGS join_use_nulls = 1")
    assert safe == (f"SELECT * FROM {DB}.take LIMIT {MAX_ROWS} SETTINGS join_use_nulls = 1")


def test_limit_is_appended_before_a_format_clause() -> None:
    # QC #2 finding G-4: `... FORMAT CSV LIMIT 200` is ClickHouse error 62.
    safe = ok(f"SELECT * FROM {DB}.take FORMAT JSONEachRow")
    assert safe == f"SELECT * FROM {DB}.take LIMIT {MAX_ROWS} FORMAT JSONEachRow"


def test_trailing_semicolon_and_comment_are_stripped_before_the_limit() -> None:
    safe = ok(f"SELECT take_id FROM {DB}.take;  -- all of them")
    assert safe == f"SELECT take_id FROM {DB}.take LIMIT {MAX_ROWS}"


# ---------------------------------------------------------------------------
# Unbounded groupArray over frame_telemetry (QC #2 finding G-3)
# ---------------------------------------------------------------------------
def test_blocks_unbounded_group_array_over_telemetry() -> None:
    reason = rejected(f"SELECT groupArray(t_s) FROM {DB}.frame_telemetry")
    assert "groupArray" in reason


@pytest.mark.parametrize(
    "fn", ["groupArray", "groupUniqArray", "groupArrayArray", "groupArraySample"]
)
def test_blocks_every_group_array_variant_over_telemetry(fn: str) -> None:
    rejected(f"SELECT {fn}(focus_score) FROM {DB}.frame_telemetry LIMIT 1")


def test_allows_the_sized_group_array_over_telemetry() -> None:
    ok(f"SELECT groupArray(50)(focus_score) FROM {DB}.frame_telemetry LIMIT 1")


def test_allows_group_array_over_a_small_table() -> None:
    # 2 500 takes cannot blow the context window; 3M telemetry rows can.
    ok(f"SELECT groupArray(take_id) FROM {DB}.take WHERE day_number = 12 LIMIT 1")


# ---------------------------------------------------------------------------
# Comment stripping / literal masking (QC #2 finding G-5)
# ---------------------------------------------------------------------------
def test_a_double_dash_inside_a_literal_survives() -> None:
    sql = f"SELECT text FROM {DB}.take_event WHERE text ILIKE '%--%' LIMIT 5"
    safe = ok(sql)
    assert "'%--%'" in safe, "the dialogue search was mangled by comment stripping"


def test_a_line_comment_is_removed_from_the_executed_sql() -> None:
    safe = ok(f"SELECT take_id -- the slate\nFROM {DB}.take LIMIT 3")
    assert "--" not in safe
    assert "the slate" not in safe


def test_a_block_comment_is_removed() -> None:
    safe = ok(f"SELECT /* pick the slate */ take_id FROM {DB}.take LIMIT 3")
    assert "/*" not in safe and "pick the slate" not in safe


def test_a_hash_comment_is_removed() -> None:
    safe = ok(f"SELECT take_id FROM {DB}.take LIMIT 3 # trailing note")
    assert "#" not in safe


def test_an_escaped_quote_inside_a_literal_does_not_unbalance_the_mask() -> None:
    sql = f"SELECT text FROM {DB}.take_event WHERE text = 'don''t drop it' LIMIT 5"
    ok(sql)


def test_a_forbidden_keyword_only_inside_a_literal_is_allowed() -> None:
    ok(f"SELECT text FROM {DB}.take_event WHERE text ILIKE '%insert into the frame%' LIMIT 5")


def test_mask_preserves_length() -> None:
    sql = "SELECT 'abc', \"col\", 'de''f'"
    assert len(guardrails._mask(sql)) == len(sql)


# ---------------------------------------------------------------------------
# Injection through a scene number, and the eval-facing helper
# ---------------------------------------------------------------------------
def test_injection_payload_inside_a_literal_is_just_text() -> None:
    ok(f"SELECT count() FROM {DB}.take WHERE scene_number = '12'' OR ''1''=''1' LIMIT 5")


def test_injection_payload_that_escapes_the_literal_is_refused() -> None:
    rejected(
        f"SELECT count() FROM {DB}.take WHERE scene_number = '12' OR '1'='1'; DROP TABLE {DB}.take"
    )


def test_validate_sql_is_the_reason_only_view() -> None:
    assert validate_sql(f"SELECT 1 FROM {DB}.take LIMIT 1") is None
    assert validate_sql("DROP TABLE slateiq.take") is not None


# ---------------------------------------------------------------------------
# Failure translation
# ---------------------------------------------------------------------------
def test_mcp_failures_get_a_crew_readable_message() -> None:
    msg = guardrails.friendly_error(
        ValueError("Tool 'run_query' not found. Available tools: transfer_to_agent")
    )
    assert "production database" in msg
    assert "run_query" not in msg


def test_other_failures_keep_their_detail_but_never_invent_a_number() -> None:
    msg = guardrails.friendly_error(RuntimeError("kaboom"))
    assert "kaboom" in msg


# A Gemini capacity blip is transient and has nothing to do with the data. QC #4
# caught the raw provider JSON -- truncated mid-sentence -- being rendered into
# the chat window on a hosted 503.
_GEMINI_503 = (
    "ServerError: 503 Service Unavailable. {'message': '{\n \"error\": {\n "
    '"code": 503,\n "message": "This model is currently experiencing '
    "high demand. Spikes in demand are usually temporary. Please try again.\"}}'}"
)


def test_model_overload_is_reported_as_busy_not_as_a_database_outage() -> None:
    msg = guardrails.friendly_error(_GEMINI_503)
    assert "busy" in msg.lower()
    # never leak the provider payload, and never blame ClickHouse/MCP
    assert "503" not in msg
    assert "ServerError" not in msg
    assert "MCP" not in msg


def test_rate_limit_is_also_a_busy_message() -> None:
    msg = guardrails.friendly_error("ClientError: 429 RESOURCE_EXHAUSTED")
    assert "busy" in msg.lower()
    assert "429" not in msg


def test_mcp_outage_still_reports_the_database() -> None:
    msg = guardrails.friendly_error(ValueError("Tool 'run_query' not found"))
    assert "MCP" in msg


# ---------------------------------------------------------------------------
# after_tool_callback truncation
# ---------------------------------------------------------------------------
def test_small_results_pass_through_untouched() -> None:
    assert guardrails._truncate_text("small") == ("small", False)


def test_large_results_are_clipped_with_an_instruction_to_re_query() -> None:
    text, clipped = guardrails._truncate_text("x" * 200_000)
    assert clipped is True
    assert "SlateIQ truncated" in text
    assert len(text) < 200_000
