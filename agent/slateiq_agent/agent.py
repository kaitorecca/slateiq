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
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import types

from . import prompts
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
    "root_agent",
    "build_clickhouse_toolset",
    "build_root_agent",
    "build_report_agent",
    "SUB_AGENT_NAMES",
]

SUB_AGENT_NAMES = (
    "editor_agent",
    "production_agent",
    "continuity_agent",
    "report_agent",
)


def build_clickhouse_toolset() -> McpToolset:
    """Create an McpToolset pointed at the ClickHouse MCP server.

    URL and bearer token come from the environment so the deployed image can
    be aimed at the hosted MCP server behind Caddy without a code change.

    ADK 2.8 note: a single McpToolset instance can be shared by several agents
    -- the toolset owns one session manager and ADK does not reparent toolsets
    the way it reparents sub-agents. We share one instance so the whole network
    holds a single MCP connection, and close it once at shutdown.
    """
    headers = {"Authorization": f"Bearer {MCP_TOKEN}"} if MCP_TOKEN else None
    logger.info("ClickHouse MCP: %s (auth=%s)", MCP_URL, bool(MCP_TOKEN))
    return McpToolset(
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
    toolset: Optional[McpToolset] = None,
) -> LlmAgent:
    return LlmAgent(
        name=name,
        model=model,
        description=description,
        instruction=instruction_fn(),
        tools=[toolset or clickhouse_toolset],
        before_tool_callback=before_tool_guardrail,
        after_tool_callback=after_tool_truncate,
        generate_content_config=_GEN_CONFIG,
    )


def build_editor_agent(toolset: Optional[McpToolset] = None) -> LlmAgent:
    return _specialist(
        "editor_agent",
        "Assistant editor. Take search, best/circled takes, dialogue line "
        "search, technical flags (boom in shot, soft focus, audio clips), "
        "emotional intensity. Returns take ids, clip URIs and timestamps.",
        prompts.editor_instruction,
        toolset=toolset,
    )


def build_production_agent(toolset: Optional[McpToolset] = None) -> LlmAgent:
    return _specialist(
        "production_agent",
        "1st AD / UPM analyst. Schedule health, pages planned vs shot, "
        "shooting ratio, setups, scenes at risk, wrap and overtime trend, "
        "forecast of remaining days.",
        prompts.production_instruction,
        toolset=toolset,
    )


def build_continuity_agent(toolset: Optional[McpToolset] = None) -> LlmAgent:
    return _specialist(
        "continuity_agent",
        "Script supervisor. Cross-take continuity conflicts for a scene and "
        "line-reading variations against the script.",
        prompts.continuity_instruction,
        toolset=toolset,
    )


def build_report_agent(toolset: Optional[McpToolset] = None) -> LlmAgent:
    return _specialist(
        "report_agent",
        "Production office. Generates the Daily Progress Report and the "
        "Editor's Log in industry Markdown format from live queries.",
        prompts.report_instruction,
        model=REPORT_MODEL,
        toolset=toolset,
    )


def build_root_agent(toolset: Optional[McpToolset] = None) -> LlmAgent:
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
