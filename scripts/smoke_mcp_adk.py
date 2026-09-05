import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import types

ts = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8765/mcp", timeout=30, sse_read_timeout=300
    )
)
agent = LlmAgent(
    name="smoke",
    model="gemini-3.5-flash",
    instruction="You query ClickHouse via tools. Be brief.",
    tools=[ts],
)


async def main():
    r = InMemoryRunner(agent=agent, app_name="smoke")
    s = await r.session_service.create_session(app_name="smoke", user_id="u")
    async for ev in r.run_async(
        user_id="u",
        session_id=s.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="List databases, then run SELECT version(). Report both.")],
        ),
    ):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.function_call:
                    print("CALL", p.function_call.name, dict(p.function_call.args))
                if p.text and ev.is_final_response():
                    print("FINAL", p.text)


asyncio.run(main())
