"""Runner plumbing shared by the FastAPI app and the eval harness.

Keeps one Runner per agent-name so the MCP session is reused across requests,
and normalises ADK events into a small, UI-friendly event shape:

    {"type": "text",        "delta": "..."}
    {"type": "tool_call",   "name": "run_query", "args": {...}, "id": "..."}
    {"type": "tool_result", "name": "run_query", "summary": "...", "rows": n}
    {"type": "agent",       "name": "editor_agent"}
    {"type": "final",       "text": "...", "sql": [...], "takes": [...]}
    {"type": "error",       "message": "..."}
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, AsyncIterator, Optional

from google.adk.agents import LlmAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.genai import types

from .agent import build_report_agent, build_root_agent, root_agent
from .config import APP_NAME, SESSION_DB_URI

_FENCE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)

_session_service = None
_runners: dict[str, Runner] = {}


def get_session_service():
    """Sqlite-backed sessions, falling back to memory if the DB is unusable."""
    global _session_service
    if _session_service is None:
        try:
            _session_service = DatabaseSessionService(db_url=SESSION_DB_URI)
        except Exception:  # pragma: no cover - e.g. read-only container FS
            _session_service = InMemorySessionService()
    return _session_service


_AGENT_BUILDERS = {
    "coordinator": lambda: root_agent,
    "report": build_report_agent,
}


def get_runner(agent_key: str = "coordinator") -> Runner:
    """Return (and cache) a Runner for one of the named entry points."""
    if agent_key not in _runners:
        builder = _AGENT_BUILDERS.get(agent_key)
        if builder is None:
            raise KeyError(f"unknown agent '{agent_key}'")
        agent: LlmAgent = builder()
        _runners[agent_key] = Runner(
            app_name=f"{APP_NAME}_{agent_key}",
            agent=agent,
            session_service=get_session_service(),
        )
    return _runners[agent_key]


async def ensure_session(
    runner: Runner, user_id: str, session_id: Optional[str]
) -> str:
    """Get or create a session id for this user."""
    if session_id:
        existing = await runner.session_service.get_session(
            app_name=runner.app_name, user_id=user_id, session_id=session_id
        )
        if existing is not None:
            return existing.id
    created = await runner.session_service.create_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )
    return created.id


def _summarise_tool_result(payload: Any, limit: int = 900) -> tuple[str, int]:
    """Human-readable one-liner + a best-effort row count."""
    rows = -1
    try:
        obj = payload
        if isinstance(obj, dict) and "result" in obj and len(obj) <= 2:
            obj = obj["result"]
        if isinstance(obj, str):
            try:
                obj = json.loads(obj)
            except Exception:
                pass
        if isinstance(obj, list):
            rows = len(obj)
        elif isinstance(obj, dict):
            for key in ("rows", "data", "result", "content"):
                if isinstance(obj.get(key), list):
                    rows = len(obj[key])
                    break
        text = json.dumps(obj, default=str)
    except Exception:
        text = str(payload)
    if len(text) > limit:
        text = text[:limit] + f" ... [{len(text)} chars]"
    return text, rows


def parse_structured_block(text: str) -> dict[str, Any]:
    """Pull the trailing ```json {...}``` UI contract block out of an answer."""
    matches = _FENCE.findall(text or "")
    if not matches:
        return {}
    try:
        obj = json.loads(matches[-1])
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


async def stream_agent(
    message: str,
    *,
    user_id: str = "web",
    session_id: Optional[str] = None,
    agent_key: str = "coordinator",
    stream_text: bool = True,
    max_llm_calls: int = 40,
) -> AsyncIterator[dict[str, Any]]:
    """Run the agent and yield normalised events.

    With ``stream_text`` the model's tokens arrive as partial events, so the UI
    can type the answer out while the SQL trace is still filling in.
    """
    runner = get_runner(agent_key)
    sid = await ensure_session(runner, user_id, session_id)
    yield {"type": "session", "session_id": sid, "agent": agent_key}

    content = types.Content(role="user", parts=[types.Part(text=message)])
    run_config = RunConfig(
        streaming_mode=StreamingMode.SSE if stream_text else StreamingMode.NONE,
        max_llm_calls=max_llm_calls,
    )
    final_text = ""
    sql: list[str] = []
    seen_agent: Optional[str] = None
    call_names: dict[str, str] = {}
    # In SSE streaming mode ADK emits each function call twice (once on the
    # partial event, once on the aggregated one) -- emit it to the UI once.
    emitted_calls: set[str] = set()

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=sid,
            new_message=content,
            run_config=run_config,
        ):
            if event.author and event.author != seen_agent:
                seen_agent = event.author
                yield {"type": "agent", "name": seen_agent}

            if not (event.content and event.content.parts):
                continue

            for part in event.content.parts:
                fc = getattr(part, "function_call", None)
                if fc is not None:
                    args = dict(fc.args or {})
                    cid = fc.id or str(uuid.uuid4())
                    if cid in emitted_calls:
                        continue
                    emitted_calls.add(cid)
                    call_names[cid] = fc.name
                    if fc.name == "run_query" and args.get("query"):
                        sql.append(args["query"])
                    yield {
                        "type": "tool_call",
                        "id": cid,
                        "name": fc.name,
                        "args": args,
                        "agent": seen_agent,
                    }
                    continue

                fr = getattr(part, "function_response", None)
                if fr is not None:
                    summary, rows = _summarise_tool_result(fr.response)
                    yield {
                        "type": "tool_result",
                        "id": fr.id or "",
                        "name": fr.name or call_names.get(fr.id or "", ""),
                        "rows": rows,
                        "summary": summary,
                        "agent": seen_agent,
                    }
                    continue

                if part.text:
                    if event.partial:
                        yield {
                            "type": "text",
                            "delta": part.text,
                            "agent": seen_agent,
                        }
                    elif event.is_final_response():
                        # Complete turn: keep the last one as the answer.
                        final_text = part.text
                    elif not stream_text:
                        yield {
                            "type": "text",
                            "delta": part.text,
                            "agent": seen_agent,
                        }
    except Exception as exc:  # surface failures to the UI instead of hanging
        yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
        return

    structured = parse_structured_block(final_text)
    yield {
        "type": "final",
        "text": final_text,
        "session_id": sid,
        "agent": seen_agent,
        "sql": structured.get("sql") or sql,
        "takes": structured.get("takes") or [],
    }


async def run_once(
    message: str,
    *,
    user_id: str = "api",
    session_id: Optional[str] = None,
    agent_key: str = "coordinator",
) -> dict[str, Any]:
    """Collect a full run into one result dict (used by /api/report + evals)."""
    events: list[dict[str, Any]] = []
    final: dict[str, Any] = {}
    async for ev in stream_agent(
        message,
        user_id=user_id,
        session_id=session_id,
        agent_key=agent_key,
        stream_text=False,
    ):
        events.append(ev)
        if ev["type"] == "final":
            final = ev
    tool_calls = [e for e in events if e["type"] == "tool_call"]
    return {
        "text": final.get("text", ""),
        "sql": final.get("sql", []),
        "takes": final.get("takes", []),
        "session_id": final.get("session_id"),
        "events": events,
        "tool_calls": [{"name": e["name"], "args": e["args"]} for e in tool_calls],
        "ran_query": any(e["name"] == "run_query" for e in tool_calls),
        "error": next(
            (e["message"] for e in events if e["type"] == "error"), None
        ),
    }
