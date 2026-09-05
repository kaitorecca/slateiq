"""Tool-level guardrails for the ClickHouse MCP toolset.

`before_tool_callback` refuses anything that is not a single read-only SELECT
(returning a dict short-circuits the tool call and feeds the dict back to the
model as the tool result). `after_tool_callback` truncates oversized results so
one runaway query cannot blow the context window.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from .config import MAX_ROWS, MAX_TOOL_RESULT_CHARS

# Statement keywords that must never reach ClickHouse from the agent path.
# Words that can never legitimately appear in a read-only SELECT. Words that
# collide with ClickHouse function names (replace, position, set...) are left
# out deliberately -- multi-statement input is already blocked, so they cannot
# form a statement of their own.
_FORBIDDEN = re.compile(
    r"\b("
    r"insert\s+into|update|delete\s+from|drop|truncate|alter\s+table|"
    r"create\s+(table|database|view|user|dictionary)|rename\s+table|attach|"
    r"detach|optimize\s+table|grant|revoke|kill\s+query|"
    r"system\s+(stop|start|flush|reload|drop|sync|restart|shutdown)"
    r")\b",
    re.IGNORECASE,
)

_COMMENT = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)
_LIMIT = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)
_AGGREGATE_ONLY = re.compile(
    r"^\s*select\b(?!.*\bfrom\b)", re.IGNORECASE | re.DOTALL
)


def _strip(sql: str) -> str:
    """Remove comments and trailing semicolons for analysis."""
    s = _COMMENT.sub(" ", sql)
    return s.strip().rstrip(";").strip()


def _deny(reason: str, sql: str) -> dict[str, Any]:
    return {
        "error": "SlateIQ guardrail rejected this query",
        "reason": reason,
        "rejected_sql": sql[:800],
        "hint": (
            "Only a single read-only SELECT (or WITH ... SELECT) statement is "
            f"allowed, and it must end with LIMIT <= {MAX_ROWS}. Rewrite the "
            "query and try again."
        ),
    }


def enforce(sql: str) -> tuple[Optional[str], str]:
    """Validate and normalise SQL.

    Returns ``(error_reason, safe_sql)``. When ``error_reason`` is None the
    returned SQL is what should actually be sent to ClickHouse -- a missing
    LIMIT is appended and an oversized LIMIT is clamped rather than rejected,
    so the model does not burn a round-trip on a recoverable mistake.
    """
    if not sql or not sql.strip():
        return "empty query", sql
    body = _strip(sql)
    lowered = body.lower()

    if ";" in body:
        return "multiple statements are not allowed", sql

    if not (lowered.startswith("select") or lowered.startswith("with")):
        return "query must start with SELECT or WITH", sql

    if lowered.startswith("with") and not re.search(r"\bselect\b", lowered):
        return "WITH block does not contain a SELECT", sql

    forbidden = _FORBIDDEN.search(body)
    if forbidden:
        return f"forbidden statement '{forbidden.group(1).upper()}' in query", sql

    if re.search(r"\binto\s+outfile\b", lowered) or re.search(
        r"\bformat\s+\w*file\b", lowered
    ):
        return "file output is not allowed", sql

    return None, _apply_limit(body)


def _apply_limit(body: str) -> str:
    """Ensure the statement ends with LIMIT <= MAX_ROWS."""
    # A SETTINGS clause must stay last, so split it off first.
    settings = ""
    m = re.search(r"\bsettings\b", body, re.IGNORECASE)
    if m:
        settings = " " + body[m.start():].strip()
        body = body[: m.start()].rstrip()

    limits = list(_LIMIT.finditer(body))
    if limits:
        last = limits[-1]
        # Only clamp a trailing LIMIT (a LIMIT inside a subquery is the
        # model's business as long as the outer one is bounded).
        if body[last.end():].strip() == "" and int(last.group(1)) > MAX_ROWS:
            body = body[: last.start(1)] + str(MAX_ROWS) + body[last.end(1):]
        elif body[last.end():].strip() != "":
            body = f"{body} LIMIT {MAX_ROWS}"
    elif not _AGGREGATE_ONLY.match(body):
        body = f"{body} LIMIT {MAX_ROWS}"
    return body + settings


def validate_sql(sql: str) -> Optional[str]:
    """Back-compat helper used by the evals: error reason or None."""
    return enforce(sql)[0]


def before_tool_guardrail(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict[str, Any]]:
    """Reject non-SELECT SQL before it reaches the MCP server."""
    if tool.name != "run_query":
        return None
    sql = args.get("query") or args.get("sql") or ""
    reason, safe_sql = enforce(sql)
    if reason:
        return _deny(reason, sql)
    if safe_sql != sql:
        # Rewrite in place so the bounded query is what actually executes.
        args["query"] = safe_sql
        sql = safe_sql
    # Record the SQL on session state so the UI / evals can show the trace.
    try:
        trace = list(tool_context.state.get("slateiq_sql", []))
        trace.append(sql)
        tool_context.state["slateiq_sql"] = trace[-25:]
    except Exception:  # pragma: no cover - state is best-effort telemetry
        pass
    return None


def _truncate_text(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text, False
    keep = MAX_TOOL_RESULT_CHARS
    return (
        text[:keep]
        + f"\n\n... [SlateIQ truncated {len(text) - keep} characters. "
        "Re-run with tighter filters, fewer columns, or an aggregate.]",
        True,
    )


def after_tool_truncate(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: Any,
) -> Optional[dict[str, Any]]:
    """Clamp huge tool results so they cannot exhaust the context window."""
    try:
        raw = (
            tool_response
            if isinstance(tool_response, str)
            else json.dumps(tool_response, default=str)
        )
    except Exception:
        return None
    if len(raw) <= MAX_TOOL_RESULT_CHARS:
        return None
    clipped, _ = _truncate_text(raw)
    return {"truncated": True, "result": clipped}
