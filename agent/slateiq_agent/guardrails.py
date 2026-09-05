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

from .config import MAX_QUERIES, MAX_QUERIES_REPORT, MAX_ROWS, MAX_TOOL_RESULT_CHARS

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

_COMMENT = re.compile(r"(--[^\n]*|#[^\n]*|/\*.*?\*/)", re.DOTALL)
_LIMIT = re.compile(r"\blimit\s+(\d+)", re.IGNORECASE)
_AGGREGATE_ONLY = re.compile(
    r"^\s*select\b(?!.*\bfrom\b)", re.IGNORECASE | re.DOTALL
)

# A single-quoted SQL literal, honouring both '' and \' escaping.
_STRING = re.compile(r"'(?:''|\\.|[^'\\])*'", re.DOTALL)

# ClickHouse's `system` database exposes query_log (every query anyone ran),
# users, grants, settings, disks, zookeeper... None of it is production data,
# all of it is information disclosure through a chat box. The MCP session runs
# with readonly=1, which stops writes but NOT reads, so this has to be blocked
# on our side.
_SYSTEM_DB = re.compile(r"(?<![\w.])system\s*\.", re.IGNORECASE)

# Table functions that read from outside ClickHouse: local files, arbitrary
# URLs (SSRF -> cloud metadata endpoints), other databases. readonly=1 happens
# to reject them today, but a hosted deployment with a differently configured
# user must not depend on that.
_TABLE_FUNCTIONS = re.compile(
    r"\b("
    r"url|urlCluster|file|fileCluster|remote|remoteSecure|cluster|"
    r"clusterAllReplicas|s3|s3Cluster|gcs|azureBlobStorage|hdfs|hdfsCluster|"
    r"mysql|postgresql|sqlite|mongodb|redis|jdbc|odbc|executable|"
    r"deltaLake|iceberg|hudi|input"
    r")\s*\(",
    re.IGNORECASE,
)

# `groupArray(x)` over frame_telemetry collapses 3M rows into ONE row that
# LIMIT cannot bound -- a 60 MB tool result. The sized form `groupArray(100)(x)`
# is fine.
_UNBOUNDED_ARRAY = re.compile(
    r"\bgroup(?:Uniq)?Array(?:Array|Insert|Sample)?\s*\(\s*(?![0-9])",
    re.IGNORECASE,
)

# A trailing FORMAT / SETTINGS clause must stay last -- LIMIT cannot follow it.
_TAIL_CLAUSE = re.compile(r"\b(settings|format)\b", re.IGNORECASE)


def _mask(sql: str) -> str:
    """Blank out string literals, preserving length so offsets stay valid.

    Keyword checks run against the masked text so that a scene slug like
    "INT. SYSTEM CORE" or a dialogue search for "%drop%" cannot trip a rule,
    and so that a `--` inside a literal is not mistaken for a comment.
    """
    return _STRING.sub(lambda m: "'" + ("x" * (len(m.group(0)) - 2)) + "'", sql)


def _strip(sql: str) -> tuple[str, str]:
    """Return ``(body, masked_body)`` with comments and trailing ``;`` removed.

    Comments are located in the *masked* text so a literal containing ``--``
    survives intact, then cut from the original at the same offsets.
    """
    masked = _mask(sql)
    out: list[str] = []
    last = 0
    for m in _COMMENT.finditer(masked):
        out.append(sql[last : m.start()])
        out.append(" ")
        last = m.end()
    out.append(sql[last:])
    body = "".join(out).strip().rstrip(";").strip()
    return body, _mask(body)


def _deny(reason: str, sql: str) -> dict[str, Any]:
    return {
        "error": "SlateIQ guardrail rejected this query",
        "reason": reason,
        "rejected_sql": sql[:800],
        "hint": (
            "Only a single read-only SELECT (or WITH ... SELECT) over the "
            f"`slateiq` database is allowed, capped at {MAX_ROWS} rows. Rewrite "
            "the query against the production tables and try again. Tell the "
            "user plainly what you cannot do -- do not retry the same query."
        ),
    }


# --------------------------------------------------------------------------
# Failure translation
# --------------------------------------------------------------------------

_MCP_HINTS = (
    "tool 'run_query' not found",
    "connect",
    "connection",
    "timeout",
    "timed out",
    "econnrefused",
    "session",
    "mcp",
)

_FRIENDLY_MCP = (
    "I can't reach the production database right now (the ClickHouse MCP "
    "server is not responding), so I won't guess at numbers. Give it a few "
    "seconds and ask me again -- if it keeps failing, whoever is running the "
    "stack needs to restart the MCP server."
)

# Gemini capacity blips (503 UNAVAILABLE / 429 RESOURCE_EXHAUSTED) are
# transient and have nothing to do with the data. Shipping the raw provider
# JSON -- truncated mid-sentence -- into the chat window reads like a broken
# product; it is a "try again" and should say so.
_MODEL_BUSY_HINTS = (
    "503",
    "429",
    "unavailable",
    "resource_exhausted",
    "resource exhausted",
    "experiencing high demand",
    "overloaded",
    "rate limit",
    "quota exceeded",
)

_FRIENDLY_MODEL_BUSY = (
    "The Gemini model is busy right now (the API returned a temporary "
    "capacity error), so the question never reached the database. Nothing is "
    "wrong with the data -- ask again in a few seconds and it will run."
)


def friendly_error(exc: BaseException | str) -> str:
    """Turn a runtime failure into something a crew member can act on.

    ADK raises a bare ``ValueError: Tool 'run_query' not found`` (plus a
    developer checklist about hallucinated function names) when the MCP
    toolset cannot list its tools -- i.e. whenever the MCP server is down.
    Shipping that to the chat window is not an acceptable answer on set.
    """
    text = exc if isinstance(exc, str) else f"{type(exc).__name__}: {exc}"
    low = text.lower()
    # Checked before the MCP hints: a Gemini 503 body often mentions
    # "connection"-ish words, and a capacity blip must not be reported as a
    # database outage.
    if any(h in low for h in _MODEL_BUSY_HINTS):
        return _FRIENDLY_MODEL_BUSY
    if any(h in low for h in _MCP_HINTS):
        return _FRIENDLY_MCP
    return (
        "Something went wrong answering that and I'd rather say so than make "
        f"a number up. Try rephrasing, or ask a narrower question. ({text[:200]})"
    )


def enforce(sql: str) -> tuple[Optional[str], str]:
    """Validate and normalise SQL.

    Returns ``(error_reason, safe_sql)``. When ``error_reason`` is None the
    returned SQL is what should actually be sent to ClickHouse -- a missing
    LIMIT is appended and an oversized LIMIT is clamped rather than rejected,
    so the model does not burn a round-trip on a recoverable mistake.
    """
    if not sql or not sql.strip():
        return "empty query", sql
    body, masked = _strip(sql)
    lowered = masked.lower()

    if ";" in masked:
        return "multiple statements are not allowed", sql

    if not (lowered.startswith("select") or lowered.startswith("with")):
        return "query must start with SELECT or WITH", sql

    if lowered.startswith("with") and not re.search(r"\bselect\b", lowered):
        return "WITH block does not contain a SELECT", sql

    forbidden = _FORBIDDEN.search(masked)
    if forbidden:
        return f"forbidden statement '{forbidden.group(1).upper()}' in query", sql

    if _SYSTEM_DB.search(masked):
        return (
            "the `system` database is out of bounds -- query the production "
            "tables in `slateiq` instead"
        ), sql

    tf = _TABLE_FUNCTIONS.search(masked)
    if tf:
        return (
            f"table function '{tf.group(1)}()' reads from outside ClickHouse "
            "and is not allowed"
        ), sql

    if re.search(r"\bframe_telemetry\b", lowered) and _UNBOUNDED_ARRAY.search(
        masked
    ):
        return (
            "an unbounded groupArray over frame_telemetry returns millions of "
            "values in a single row that LIMIT cannot bound -- use the sized "
            "form groupArray(50)(col), or aggregate with avg/count/countIf"
        ), sql

    if re.search(r"\binto\s+outfile\b", lowered) or re.search(
        r"\bformat\s+\w*file\b", lowered
    ):
        return "file output is not allowed", sql

    return None, _apply_limit(body, masked)


def _apply_limit(body: str, masked: str = "") -> str:
    """Ensure the statement ends with LIMIT <= MAX_ROWS.

    ``masked`` is the same string with literals blanked out (and therefore the
    same length), so a FORMAT/SETTINGS keyword inside a literal is not mistaken
    for the real tail clause.
    """
    masked = masked or _mask(body)
    # FORMAT and SETTINGS must stay last -- `... FORMAT CSV LIMIT 200` is a
    # ClickHouse syntax error -- so split the tail off before touching LIMIT.
    tail = ""
    m = _TAIL_CLAUSE.search(masked)
    if m:
        tail = " " + body[m.start():].strip()
        body = body[: m.start()].rstrip()
        masked = masked[: m.start()].rstrip()

    limits = list(_LIMIT.finditer(masked))
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
    return body + tail


def validate_sql(sql: str) -> Optional[str]:
    """Back-compat helper used by the evals: error reason or None."""
    return enforce(sql)[0]


def _budget_for(agent_name: str) -> int:
    return MAX_QUERIES_REPORT if "report" in (agent_name or "") else MAX_QUERIES


def _over_budget(tool_context: ToolContext) -> Optional[dict[str, Any]]:
    """Hard cap on `run_query` calls within one user turn.

    The instructions ask for query economy and the model mostly obeys, but on
    open-ended questions ("did the dialogue change?", "do they share a common
    cause?") it will keep digging long after the answer is in hand -- 17-19
    queries and four minutes, when the first grouped query already said it.
    A prompt cannot reliably stop that; a counter can. When the budget is
    spent the model gets a tool result telling it to answer from what it has,
    which is exactly the behaviour we want.
    """
    try:
        inv = tool_context.invocation_id or ""
        budget = _budget_for(getattr(tool_context, "agent_name", ""))
        state = tool_context.state.get("slateiq_query_budget") or {}
        used = int(state.get("used", 0)) if state.get("inv") == inv else 0
        if used >= budget:
            return {
                "error": "SlateIQ query budget reached",
                "reason": (
                    f"this turn has already run {used} queries (limit {budget})"
                ),
                "hint": (
                    "Stop querying and answer now from the results you already "
                    "have. Say plainly if something is still unknown -- a "
                    "partial answer with its gaps named is useful; another "
                    "query is not."
                ),
            }
        tool_context.state["slateiq_query_budget"] = {"inv": inv, "used": used + 1}
    except Exception:  # pragma: no cover - never let accounting break a query
        return None
    return None


def before_tool_guardrail(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict[str, Any]]:
    """Reject non-SELECT SQL before it reaches the MCP server."""
    if tool.name != "run_query":
        return None
    spent = _over_budget(tool_context)
    if spent is not None:
        return spent
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
