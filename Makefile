# SlateIQ — one-command reproducibility.
# Everything here is the exact command the README documents; nothing is hidden.
# Prereqs: the two virtualenvs (.venv, .venv-mcp), a local ClickHouse, and .env.
# See "Run it locally" in README.md for the one-time setup.

SHELL     := /bin/bash
PY        := .venv/bin/python
PIP       := .venv/bin/python -m pip
API_PORT  ?= 8811
WEB_PORT  ?= 5188
MCP_PORT  ?= 8765

.DEFAULT_GOAL := help
.PHONY: help venvs mcp api web test verify eval lint fmt build deploy

help:  ## show this list
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk -F':.*?## ' '{printf "  \033[1m%-8s\033[0m %s\n", $$1, $$2}'

venvs:  ## create .venv (agent + pipeline + dev tools) and .venv-mcp; run once
	python3 -m venv .venv
	$(PIP) install -q -r agent/requirements.txt -r ingest/requirements.txt \
	                  -r requirements-dev.txt
	python3 -m venv .venv-mcp
	.venv-mcp/bin/python -m pip install -q 'mcp-clickhouse==0.6.0'

mcp:  ## start the official mcp-clickhouse server on :8765 (data path for every agent)
	CLICKHOUSE_MCP_BIND_PORT=$(MCP_PORT) scripts/mcp_up.sh

api:  ## run the agent + UI on :8811  (/ app, /dev-ui/ ADK dev UI, /docs OpenAPI)
	set -a; source .env; set +a; \
	cd agent && ../.venv/bin/uvicorn main:app --port $(API_PORT)

web:  ## Vite dev server on :5188 with hot reload, proxying /api to :8811
	cd web && npm install && npm run dev

test:  ## unit tests (116, no network, no ClickHouse)
	$(PY) -m pytest agent/tests -q

verify:  ## 43 assertions over the seeded ClickHouse: schema, MVs, 15 golden queries
	set -a; source .env; set +a; $(PY) db/verify.py

eval:  ## 28 judged questions through the real coordinator + real MCP (costs Gemini calls)
	set -a; source .env; set +a; $(PY) agent/evals/run_eval.py

lint:  ## ruff check (must be clean) + tsc --noEmit
	$(PY) -m ruff check agent ingest db scripts
	$(PY) -m ruff format --check agent ingest db scripts
	@if [ -d web/node_modules ]; then \
	  cd web && npx tsc --noEmit; \
	else \
	  echo "skipping tsc --noEmit: run 'cd web && npm ci' first"; \
	fi

fmt:  ## apply ruff's safe fixes and formatting
	$(PY) -m ruff check agent ingest db scripts --fix
	$(PY) -m ruff format agent ingest db scripts

build:  ## production build of the SPA into web/dist (committed, baked into the image)
	cd web && npm install && npm run build

deploy:  ## rebuild + roll out the Cloud Run service (agent + UI)
	bash deploy/cloudrun/deploy_agent.sh
