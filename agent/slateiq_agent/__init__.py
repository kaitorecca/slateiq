"""SlateIQ ADK agent package.

`root_agent` is the ADK entry point discovered by `adk web` and by
`google.adk.cli.fast_api.get_fast_api_app(agents_dir=...)`.
"""

from .agent import (
    build_clickhouse_toolset,
    build_continuity_agent,
    build_editor_agent,
    build_production_agent,
    build_report_agent,
    build_root_agent,
    clickhouse_toolset,
    root_agent,
)

__all__ = [
    "build_clickhouse_toolset",
    "build_continuity_agent",
    "build_editor_agent",
    "build_production_agent",
    "build_report_agent",
    "build_root_agent",
    "clickhouse_toolset",
    "root_agent",
]
