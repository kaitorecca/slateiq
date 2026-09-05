"""Runtime configuration for the SlateIQ agent network.

Everything that differs between local dev and the hosted deployment comes from
environment variables so the same image can point at a remote ClickHouse MCP
server.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Repo layout ------------------------------------------------------------
# agent/slateiq_agent/config.py -> agent/ -> repo root
PKG_DIR = Path(__file__).resolve().parent
AGENT_DIR = PKG_DIR.parent
REPO_ROOT = AGENT_DIR.parent


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


# --- Models -----------------------------------------------------------------
# Sub-agents run on flash for speed/cost; the report agent may be upgraded.
MODEL = _env("SLATEIQ_MODEL", "gemini-3.5-flash")
REPORT_MODEL = _env("SLATEIQ_REPORT_MODEL", MODEL)
TTS_MODEL = _env("SLATEIQ_TTS_MODEL", "gemini-2.5-flash-preview-tts")
TTS_VOICE = _env("SLATEIQ_TTS_VOICE", "Kore")

# --- ClickHouse MCP ---------------------------------------------------------
# The ONLY path the agents use to reach data. Never bypassed for reasoning.
MCP_URL = _env("CLICKHOUSE_MCP_URL", "http://localhost:8765/mcp")
MCP_TOKEN = _env("CLICKHOUSE_MCP_TOKEN")
MCP_TIMEOUT = float(_env("CLICKHOUSE_MCP_TIMEOUT", "30"))
# Read-gap timeout on the MCP stream. If the MCP server is restarted under a
# live toolset the cached session goes quiet rather than erroring, and this
# is what eventually unsticks it -- 300s meant the first request after an
# MCP restart hung for five minutes. 120s is still far longer than any
# single query takes (the slowest full-telemetry scan is ~2s).
MCP_SSE_READ_TIMEOUT = float(_env("CLICKHOUSE_MCP_SSE_READ_TIMEOUT", "120"))

# --- Database ---------------------------------------------------------------
DB = _env("SLATEIQ_DB", "slateiq")

# --- Guardrails -------------------------------------------------------------
MAX_ROWS = int(_env("SLATEIQ_MAX_ROWS", "200"))
MAX_TOOL_RESULT_CHARS = int(_env("SLATEIQ_MAX_TOOL_RESULT_CHARS", "24000"))

# --- Media ------------------------------------------------------------------
CLIPS_DIR = _env("CLIPS_DIR", str(REPO_ROOT / "data" / "clips"))
WEB_DIST = _env("SLATEIQ_WEB_DIST", str(REPO_ROOT / "web" / "dist"))

# --- Sessions ---------------------------------------------------------------
SESSION_DB_URI = _env(
    "SLATEIQ_SESSION_DB_URI", f"sqlite:///{AGENT_DIR / 'sessions.db'}"
)

APP_NAME = "slateiq_agent"
