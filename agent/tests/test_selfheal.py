"""The MCP toolset must survive a restart of `mcp-clickhouse`.

Covers the decision the wrapper makes -- retry a broken pipe, never retry a
ClickHouse error -- with a fake tool instead of a real MCP server.
"""

from __future__ import annotations

import pytest
from slateiq_agent.agent import SelfHealingMcpToolset, _is_transport_failure


@pytest.mark.parametrize(
    "text",
    [
        "Failed to get tools from MCP server: Session terminated",
        "ConnectionError: [Errno 111] Connection refused",
        "httpx.ReadTimeout",
        "anyio.BrokenResourceError: transport closed",
        "HTTP 503 Bad Gateway",
    ],
)
def test_transport_failures_are_recognised(text: str) -> None:
    assert _is_transport_failure(text)


@pytest.mark.parametrize(
    "text",
    [
        "Code: 47. DB::Exception: Unknown expression identifier 'sceen_number'",
        "Code: 62. DB::Exception: Syntax error near FORMAT",
        "SlateIQ guardrail rejected this query",
        "",
    ],
)
def test_query_errors_are_not_retried(text: str) -> None:
    # Retrying a bad query would burn a round-trip and hide the error the model
    # needs to read.
    assert not _is_transport_failure(text)


class _FakeTool:
    """Stands in for an ADK McpTool: fails n times, then succeeds."""

    name = "run_query"

    def __init__(self, failures: list):
        self.failures = failures
        self.calls = 0

    async def run_async(self, *, args, tool_context):
        self.calls += 1
        if self.failures:
            failure = self.failures.pop(0)
            if isinstance(failure, Exception):
                raise failure
            return failure
        return {"rows": [[1]]}


class _Toolset(SelfHealingMcpToolset):
    """Counts resets instead of touching a real session manager."""

    def __init__(self):
        self.resets = 0

    async def _reset_session(self) -> None:
        self.resets += 1


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def test_a_dead_session_is_retried_once_against_a_fresh_one() -> None:
    ts = _Toolset()
    tool = _FakeTool([{"error": "MCP tool execution failed: Session terminated"}])
    healed = ts._heal(tool)
    result = _run(healed.run_async(args={"query": "SELECT 1"}, tool_context=None))
    assert result == {"rows": [[1]]}
    assert tool.calls == 2 and ts.resets == 1


def test_a_raised_transport_crash_is_retried_too() -> None:
    ts = _Toolset()
    tool = _FakeTool([ConnectionError("peer closed connection")])
    healed = ts._heal(tool)
    assert _run(healed.run_async(args={}, tool_context=None)) == {"rows": [[1]]}
    assert tool.calls == 2 and ts.resets == 1


def test_a_clickhouse_error_is_handed_back_untouched() -> None:
    ts = _Toolset()
    err = {"error": "Code: 47. DB::Exception: Unknown identifier 'sceen'"}
    tool = _FakeTool([err])
    healed = ts._heal(tool)
    assert _run(healed.run_async(args={}, tool_context=None)) == err
    assert tool.calls == 1 and ts.resets == 0


def test_a_healthy_call_is_not_wrapped_twice() -> None:
    ts = _Toolset()
    tool = _FakeTool([])
    once = ts._heal(tool)
    twice = ts._heal(once)
    assert twice is once
    assert _run(twice.run_async(args={}, tool_context=None)) == {"rows": [[1]]}
    assert tool.calls == 1 and ts.resets == 0
