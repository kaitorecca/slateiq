# SlateIQ agent + API.
#
# Build context is the REPO ROOT (we need db/SCHEMA.md and web/dist):
#   docker build -f agent/Dockerfile -t slateiq-agent .
#
# Run:
#   docker run -p 8080:8080 --env-file .env \
#     -e CLICKHOUSE_MCP_URL=https://mcp.example.com/mcp \
#     -e CLICKHOUSE_MCP_TOKEN=... slateiq-agent
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    SLATEIQ_SESSION_DB_URI=sqlite:////tmp/slateiq-sessions.db

WORKDIR /app

# Dependencies first so the layer caches.
COPY agent/requirements.txt /app/agent/requirements.txt
RUN pip install --no-cache-dir -r /app/agent/requirements.txt

# Agent code.
COPY agent/ /app/agent/

# Shared schema contract (owned by db/). Optional at build time -- the agent
# falls back to its embedded schema summary if it is absent.
COPY db/ /app/db/

# Built web UI, if the frontend has been built. Optional.
COPY web/ /app/web/

# Clips are normally served from GCS in production; mount or COPY if local.
ENV CLIPS_DIR=/app/data/clips
RUN mkdir -p /app/data/clips

WORKDIR /app/agent
EXPOSE 8080

# Cloud Run injects $PORT.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 600
