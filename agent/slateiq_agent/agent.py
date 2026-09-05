"""SlateIQ ADK multi-agent network.

A coordinator LlmAgent routes film-production questions to four specialists.
Every specialist reaches ClickHouse *only* through the official
`mcp-clickhouse` MCP server (StreamableHTTP), never through a direct driver --
that is the ClickHouse-track requirement and it is enforced by the fact that
these agents have no other data tool.

ADK convention: `root_agent` is what `adk web` / `get_fast_api_app` pick up.
"""

from __future__ import annotations

import logging
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import LlmResponse
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from . import prompts, report_cache
from .config import (
    MCP_SSE_READ_TIMEOUT,
    MCP_TIMEOUT,
    MCP_TOKEN,
    MCP_URL,
    MODEL,
    REPORT_MODEL,
)
from .guardrails import after_tool_truncate, before_tool_guardrail

logger = logging.getLogger(__name__)

__all__ = [
    "REPORT_REQUEST_KEY",
    "SUB_AGENT_NAMES",
    "SelfHealingMcpToolset",
    "build_clickhouse_toolset",
    "build_report_agent",
    "build_root_agent",
    "root_agent",
]

SUB_AGENT_NAMES = (
    "editor_agent",
    "production_agent",
    "continuity_agent",
    "report_agent",
)


# ---------------------------------------------------------------------------
# Self-healing MCP toolset
# ---------------------------------------------------------------------------
# ADK pools one streamable-HTTP session per toolset and reuses it for the life
# of the process. When `mcp-clickhouse` restarts (a redeploy, an OOM, the VM
# rebooting) that pooled session is dead: ADK retries *session creation*
# (`McpTool._create_session` is decorated with `retry_on_errors`) but never the
# tool call itself, so the first question asked after a restart came back as a
# developer error and only the second one worked. QC #2 flagged this and left
# it for the deploy owner -- this is that fix.
#
# The cure is small: notice a transport-shaped failure on the tool-call path,
# drop the pooled session, and run the call once more against a fresh one. A
# ClickHouse error (bad SQL, unknown column) is NOT transport-shaped and is
# never retried -- the model must see it and fix its own query.

# Substrings that mean "the pipe, not the database, is what failed".
_TRANSPORT_HINTS = (
    "session",
    "connection",
    "connect",
    "transport",
    "closed",
    "broken pipe",
    "eof",
    "peer",
    "disconnect",
    "reset by",
    "timeout",
    "timed out",
    "httpx",
    "httpcore",
    "502",
    "503",
    "504",
    "bad gateway",
)


def _is_transport_failure(text: str) -> bool:
    low = (text or "").lower()
    return any(hint in low for hint in _TRANSPORT_HINTS)


def _looks_like_error(result: Any) -> str:
    """The error text of a failed tool result, or '' if it succeeded.

    With ADK's graceful MCP error handling on (the default), a failed tool call
    comes back as ``{"error": "..."}`` instead of raising.
    """
    if isinstance(result, dict):
        err = result.get("error")
        if isinstance(err, str):
            return err
    return ""


class SelfHealingMcpToolset(McpToolset):
    """`McpToolset` that recovers on its own from an MCP server restart."""

    async def _reset_session(self) -> None:
        """Throw away the pooled MCP session so the next call opens a new one."""
        try:
            await self._mcp_session_manager.close()
            logger.warning("MCP session reset -- reconnecting to %s", MCP_URL)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("MCP session reset failed (continuing): %s", exc)

    def _heal(self, tool: Any) -> Any:
        """Wrap one MCP tool's `run_async` with reset-and-retry-once."""
        if getattr(tool, "_slateiq_self_healing", False):
            return tool
        inner = tool.run_async

        async def run_async(*, args, tool_context, **kwargs):
            try:
                result = await inner(args=args, tool_context=tool_context, **kwargs)
                err = _looks_like_error(result)
                if not err or not _is_transport_failure(err):
                    return result
                logger.warning("MCP tool %s failed on transport: %s", tool.name, err)
            except Exception as exc:  # transport crash raised rather than returned
                if not _is_transport_failure(f"{type(exc).__name__}: {exc}"):
                    raise
                logger.warning("MCP tool %s raised on transport: %s", tool.name, exc)
            # One retry against a brand-new session. The MCP tools here are
            # read-only SELECTs, so replaying one cannot duplicate a side
            # effect -- which is exactly why ADK leaves this to the caller.
            await self._reset_session()
            return await inner(args=args, tool_context=tool_context, **kwargs)

        tool.run_async = run_async
        tool._slateiq_self_healing = True
        return tool

    async def get_tools(self, readonly_context: ReadonlyContext | None = None) -> list[Any]:
        try:
            tools = await super().get_tools(readonly_context)
        except Exception as exc:
            if not _is_transport_failure(f"{type(exc).__name__}: {exc}"):
                raise
            logger.warning("MCP tool listing failed (%s) -- reconnecting", exc)
            await self._reset_session()
            tools = await super().get_tools(readonly_context)
        return [self._heal(t) for t in tools]


def build_clickhouse_toolset() -> McpToolset:
    """Create an McpToolset pointed at the ClickHouse MCP server.

    URL and bearer token come from the environment so the deployed image can
    be aimed at the hosted MCP server behind Caddy without a code change.

    ADK 2.8 note: a single McpToolset instance can be shared by several agents
    -- the toolset owns one session manager and ADK does not reparent toolsets
    the way it reparents sub-agents. We share one instance so the whole network
    holds a single MCP connection, and close it once at shutdown.

    The instance is a `SelfHealingMcpToolset` so a restart of the MCP server
    does not cost the next question.
    """
    headers = {"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else None
    logger.info("ClickHouse MCP: %s (auth=%s)", MCP_URL, bool(MCP_TOKEN))
    return SelfHealingMcpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MCP_URL,
            headers=headers,
            timeout=MCP_TIMEOUT,
            sse_read_timeout=MCP_SSE_READ_TIMEOUT,
        )
    )


# One shared MCP connection for the whole network.
clickhouse_toolset = build_clickhouse_toolset()

_GEN_CONFIG = types.GenerateContentConfig(temperature=0.2)


def _specialist(
    name: str,
    description: str,
    instruction_fn,
    model: str = MODEL,
    toolset: McpToolset | None = None,
    extra_tools: list[Any] | None = None,
    after_model_callback=None,
) -> LlmAgent:
    return LlmAgent(
        name=name,
        model=model,
        description=description,
        instruction=instruction_fn(),
        tools=[toolset or clickhouse_toolset, *(extra_tools or [])],
        before_tool_callback=before_tool_guardrail,
        after_tool_callback=after_tool_truncate,
        after_model_callback=after_model_callback,
        generate_content_config=_GEN_CONFIG,
    )


def build_editor_agent(toolset: McpToolset | None = None) -> LlmAgent:
    return _specialist(
        "editor_agent",
        "Assistant editor. Take search, best/circled takes, dialogue line "
        "search, technical flags (boom in shot, soft focus, audio clips), "
        "emotional intensity. Returns take ids, clip URIs and timestamps.",
        prompts.editor_instruction,
        toolset=toolset,
    )


def build_production_agent(toolset: McpToolset | None = None) -> LlmAgent:
    return _specialist(
        "production_agent",
        "1st AD / UPM analyst. Schedule health, pages planned vs shot, "
        "shooting ratio, setups, scenes at risk, wrap and overtime trend, "
        "forecast of remaining days.",
        prompts.production_instruction,
        toolset=toolset,
    )


def build_continuity_agent(toolset: McpToolset | None = None) -> LlmAgent:
    return _specialist(
        "continuity_agent",
        "Script supervisor. Cross-take continuity conflicts for a scene and "
        "line-reading variations against the script.",
        prompts.continuity_instruction,
        toolset=toolset,
    )


# ---------------------------------------------------------------------------
# Report cache tool (local file read -- NOT an MCP call)
# ---------------------------------------------------------------------------
# QC #4 issue #4: the DPR *button* is 0.5 s (it reads the on-disk cache that
# `/api/report/dpr` writes) while the same request typed into the chat cost
# 87 s and 13 `run_query` calls to rebuild a document that was already on
# disk. This tool gives the report agent the same cache. It reads a local
# JSON file and touches no database, so the trace shows it as an ordinary
# function tool -- never "via mcp-clickhouse". The markdown it returns was
# itself produced by MCP queries, and the prompt requires the answer to say so.

REPORT_REQUEST_KEY = "slateiq_report_request"


def get_cached_report(kind: str, day: int, tool_context: ToolContext) -> dict[str, Any]:
    """Fetch an already-generated report for a shooting day from the SlateIQ cache.

    Call this FIRST for any Daily Progress Report or Editor's Log request.

    Args:
        kind: 'dpr' for the Daily Progress Report, 'editors_log' for the Editor's Log.
        day: shooting day number, e.g. 12.

    Returns:
        found=True with the finished `markdown` and `generated_at` when the
        document is already on disk; found=False with a `reason` when it is
        not, in which case generate it from live queries as usual.
    """
    result = report_cache.get_cached_report(kind, day)
    try:
        tool_context.state[REPORT_REQUEST_KEY] = {
            "kind": result.get("kind") or report_cache.normalise_kind(kind),
            "day": result.get("day"),
            "found": bool(result.get("found")),
        }
    except Exception:  # pragma: no cover - state is best-effort
        logger.debug("could not record the report request on state")
    return result


def _cache_fresh_report(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """Write a freshly generated report to the same cache the button reads.

    The model never has to hand the markdown back a second time: when
    `get_cached_report` missed, we know the kind and day it asked for, so the
    final (non-partial, no-tool-call) answer of that turn *is* the report.
    Always returns None -- the response itself is untouched.
    """
    try:
        if getattr(llm_response, "partial", False):
            return None
        req = callback_context.state.get(REPORT_REQUEST_KEY) or {}
        if not req or not req.get("kind"):
            return None
        content = getattr(llm_response, "content", None)
        parts = list(getattr(content, "parts", None) or [])
        if any(getattr(p, "function_call", None) for p in parts):
            return None
        text = "".join(p.text for p in parts if getattr(p, "text", None))
        # The marker means this answer IS the cached document -- nothing to
        # write back. Anything else is freshly generated, including a
        # "refresh" that deliberately ignored the cache, and replaces it.
        if report_cache.CACHED_REPORT_MARKER in text:
            return None
        # A real DPR / Editor's Log is a long Markdown document with tables;
        # a one-line "which day?" clarification must never poison the cache.
        if len(text.strip()) < 600 or "|" not in text:
            return None
        if report_cache.save_cached_report(req["kind"], req["day"], text):
            logger.info("cached fresh %s for day %s", req["kind"], req["day"])
            callback_context.state[REPORT_REQUEST_KEY] = {**req, "found": True}
    except Exception as exc:  # pragma: no cover - caching is best-effort
        logger.warning("could not cache the generated report: %s", exc)
    return None


def build_report_agent(toolset: McpToolset | None = None) -> LlmAgent:
    return _specialist(
        "report_agent",
        "Production office. Generates the Daily Progress Report and the "
        "Editor's Log in industry Markdown format from live queries.",
        prompts.report_instruction,
        model=REPORT_MODEL,
        toolset=toolset,
        extra_tools=[FunctionTool(get_cached_report)],
        after_model_callback=_cache_fresh_report,
    )


def build_root_agent(toolset: McpToolset | None = None) -> LlmAgent:
    ts = toolset or clickhouse_toolset
    return LlmAgent(
        name="slateiq_coordinator",
        model=MODEL,
        description=(
            "SlateIQ coordinator -- answers film-production questions about "
            "dailies, schedule, continuity and reports from the production's "
            "ClickHouse database."
        ),
        instruction=prompts.coordinator_instruction(),
        sub_agents=[
            build_editor_agent(ts),
            build_production_agent(ts),
            build_continuity_agent(ts),
            build_report_agent(ts),
        ],
        tools=[ts],
        before_tool_callback=before_tool_guardrail,
        after_tool_callback=after_tool_truncate,
        generate_content_config=_GEN_CONFIG,
    )


root_agent = build_root_agent()
