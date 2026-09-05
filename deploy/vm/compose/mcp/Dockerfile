# Official ClickHouse MCP server (https://github.com/ClickHouse/mcp-clickhouse), HTTP transport.
FROM python:3.12-slim
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir "mcp-clickhouse==0.6.0" \
 && find /usr/local -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && useradd -m -u 10001 mcp
USER mcp
EXPOSE 8765
CMD ["python", "-m", "mcp_clickhouse.main"]
