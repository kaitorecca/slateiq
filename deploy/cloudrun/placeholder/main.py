"""Placeholder service used to validate the Cloud Run pipeline before agent/ exists.

Once agent/Dockerfile lands, deploy_agent.sh builds that instead and this file is
never deployed again. It intentionally exercises the same surface the real service
needs: PORT binding, /health, and the env/secret wiring.
"""
import os

from fastapi import FastAPI

app = FastAPI(title="SlateIQ (placeholder)")


@app.get("/health")
def health():
    return {"status": "ok", "service": "slateiq-placeholder"}


@app.get("/")
def root():
    return {
        "service": "slateiq",
        "note": "placeholder — the ADK agent replaces this once agent/Dockerfile exists",
        "wiring": {
            # Values are never echoed, only presence — this is a public endpoint.
            "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
            "CLICKHOUSE_MCP_URL": os.getenv("CLICKHOUSE_MCP_URL", ""),
            "CLICKHOUSE_MCP_TOKEN": bool(os.getenv("CLICKHOUSE_MCP_TOKEN")),
            "CLIPS_BASE_URL": os.getenv("CLIPS_BASE_URL", ""),
            "GRAFANA_URL": os.getenv("GRAFANA_URL", ""),
        },
    }
