# deploy/ — SlateIQ hosting runbook

Everything SlateIQ runs on, and how to (re)build it. Free tier only — see [cost.md](cost.md).

```
                       internet
                          |
        +-----------------+------------------+---------------------+
        |                 |                  |                     |
   Cloud Run          Cloud Run          GCS bucket          e2-micro VM (us-central1-a)
   `slateiq`        `slateiq-grafana`   slateiq-media-*      slateiq-data
   ADK agent +      Grafana OSS          clips/ thumbs/      +---------------------------+
   FastAPI + UI     anon Viewer          public read         | caddy   :80/:443/:8443    |
        |                 |                                  |   /mcp  -> mcp:8765       |
        |  MCP (https,    |  ClickHouse HTTP over TLS        |   /ch/* -> clickhouse:8123|
        |  bearer token)  |  (user agent_ro, read-only)      | mcp-clickhouse 0.6 (http) |
        +-----------------+----------------------------------> clickhouse-server 25.6   |
                                                             +---------------------------+
```

Live URLs and the current tokens: [OUTPUT.md](OUTPUT.md) (values) and `.secrets/deploy.env` (secrets, gitignored).

---

## 0. Prerequisites

```bash
gcloud auth login && gcloud config set project gke-hackathon-472816
set -a; source .env; set +a          # GOOGLE_API_KEY etc.
```

Everything below is **idempotent** — re-running a script converges rather than duplicating.
Nothing here ever deletes a resource it did not create; the VM additionally carries
`--deletion-protection`.

---

## 1. Data plane — ClickHouse + official MCP server on one free VM

```bash
deploy/vm/create_vm.sh        # e2-micro + 30 GB pd-standard + firewall (80/443/8443)
deploy/vm/deploy_stack.sh     # ships compose/, generates secrets, brings the stack up, verifies TLS
```

`create_vm.sh` passes `bootstrap.sh` as the GCE **startup-script**: it installs Docker CE +
the compose plugin, creates a 2 GiB swapfile, sets `vm.swappiness=10` /
`vm.overcommit_memory=1`, caps container logs, and restarts the stack on every boot.
The Ops Agent is deliberately **not** installed — it would cost ~120 MB of a 1 GiB box.

`deploy_stack.sh` then:
1. generates `.secrets/deploy.env` (three random secrets) on first run, and refreshes the
   derived `PUBLIC_HOST` / `CLICKHOUSE_MCP_URL` values on every run;
2. tars `deploy/vm/compose/` up to `/opt/slateiq` and writes a 0600 `.env` there;
3. `docker compose up -d --build`;
4. curls `https://<ip>.sslip.io/health`, `/ch/ping`, and an unauthenticated `POST /mcp`
   (which must return **401**).

### What runs on the VM

| Container | Image | Memory cap | Exposed |
|---|---|---|---|
| `slateiq-ch` | `clickhouse/clickhouse-server:25.6` | 620 MB | 127.0.0.1 only |
| `slateiq-mcp` | `python:3.12-slim` + `mcp-clickhouse==0.6.0` | 200 MB | internal only |
| `slateiq-caddy` | `caddy:2.10-alpine` | 80 MB | 80, 443, 8443 |

**ClickHouse on 1 GiB** (`compose/clickhouse/config.d/low-mem.xml`):
`max_server_memory_usage_to_ram_ratio 0.6`, `mark_cache_size 128 MiB`,
`uncompressed_cache_size 0`, `max_concurrent_queries 8`, background pools cut to 4/2/2,
merges capped at 1 GiB parts, and every system log except a 3-day-TTL `query_log` disabled.
Per-user limits live in `compose/clickhouse/users.d/slateiq.xml`: `max_memory_usage 400 MB`,
`max_threads 2`, spill-to-disk thresholds at 200 MB.

**Users:** `default` (admin, used only by seeding, reachable only on localhost/inside the
container) and **`agent_ro`** — `readonly=2`, `allow_ddl=0`, 30 s query timeout, 20k row result
cap, 240 queries/min quota. `agent_ro` is the only identity mcp-clickhouse and Grafana ever use.

**TLS** is Let's Encrypt via Caddy against `<ip>.sslip.io` — a free wildcard DNS service that
resolves any `<ip>.sslip.io` to that IP. No domain, no Cloud DNS zone, no managed certificate.

### Verifying by hand

```bash
H=$(grep PUBLIC_HOST .secrets/deploy.env | cut -d= -f2)
T=$(grep CLICKHOUSE_MCP_TOKEN .secrets/deploy.env | cut -d= -f2)

curl -s https://$H/health                       # -> OK
curl -s https://$H/ch/ping                      # -> Ok.
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://$H/mcp   # -> 401 (no token)

curl -s https://$H/mcp -H "Authorization: Bearer $T" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

### Operating

```bash
gcloud compute ssh slateiq-data --zone us-central1-a --command 'cd /opt/slateiq && docker compose ps'
gcloud compute ssh slateiq-data --zone us-central1-a --command 'docker logs --tail 50 slateiq-mcp'
gcloud compute ssh slateiq-data --zone us-central1-a --command 'free -m && docker stats --no-stream'
```

**If the VM is stopped and restarted its ephemeral IP changes**, and with it `PUBLIC_HOST`.
Recover with: `deploy/vm/deploy_stack.sh` then `deploy/cloudrun/deploy_agent.sh` and
`deploy/grafana/deploy.sh` (≈4 minutes; all three read the refreshed `.secrets/deploy.env`).

---

## 2. Seeding the hosted database

```bash
deploy/vm/seed_remote.sh                 # everything
deploy/vm/seed_remote.sh take take_event # a subset
DRY_RUN=1 deploy/vm/seed_remote.sh       # plan only
CHUNK_ROWS=200000 deploy/vm/seed_remote.sh   # smaller chunks if the VM struggles
```

Pipeline: local ClickHouse → `SELECT ... FORMAT Parquet` (zstd) → `gcloud compute scp` →
`INSERT ... FROM INFILE` **inside** the container → delete the file. One chunk at a time, so
local disk, VM disk and VM RAM all stay flat regardless of table size.

- **Schema** is replayed from `system.tables.create_table_query` with the Atomic UUID stripped
  and `IF NOT EXISTS` injected, base tables ordered before views — so the hosted schema is
  exactly what the agent was developed against, with no second source of truth.
- **Materialized-view targets** (`take_daily_agg`, `take_scene_agg`) are detected automatically
  and **never copied** — the MVs repopulate them when the base tables are inserted. Copying
  them too would double-count every aggregate.
- **Insert order** is `production, scene, shooting_day, take, take_analysis, take_event,
  continuity_note, frame_telemetry` so MVs fire against populated parents.
- **`frame_telemetry` (~3.07 M rows)** is split with `cityHash64(take_id) % n` — hash-modulo
  chunking works on our String take ids, needs no ORDER BY, and produces evenly sized chunks.
- Finishes with a local-vs-hosted row-count table and the hosted on-disk size.

---

## 3. Agent on Cloud Run

```bash
deploy/cloudrun/deploy_agent.sh
```

Builds `agent/Dockerfile` **with the repo root as build context** (the image needs `db/` and
`web/dist/`), pushes to Artifact Registry `slateiq`, and deploys service `slateiq`:
`--min-instances 0 --max-instances 2 --cpu 1 --memory 1Gi --concurrency 40
--allow-unauthenticated`.

`GOOGLE_API_KEY` goes to **Secret Manager** (`slateiq-google-api-key`) and is mounted as an env
var; the script destroys superseded versions so the free 6-version budget is never exceeded.
Everything else (`CLICKHOUSE_MCP_URL`, `CLICKHOUSE_MCP_TOKEN`, `CLIPS_BASE_URL`, `GRAFANA_URL`)
is read from `.secrets/deploy.env` and set as plain env vars.

If `agent/Dockerfile` is missing the script falls back to `deploy/cloudrun/placeholder/`
(a two-route FastAPI app) so the build → registry → secret-mount → public-URL pipeline can be
validated independently of the agent's readiness. It says loudly when it does this.

`deploy/cloudrun/gcloudignore.template` is copied to the repo root as `.gcloudignore` on first
build so Cloud Build never uploads `.secrets/`, `data/footage/`, `node_modules/` or the venvs.

---

## 4. Grafana on Cloud Run

```bash
deploy/grafana/deploy.sh
```

`grafana/grafana-oss` with `grafana-clickhouse-datasource` **baked into the image** (Cloud Run
has no persistent disk — installing at boot would re-download on every cold start).
Anonymous `Viewer` access, login form disabled, `GF_SECURITY_ALLOW_EMBEDDING=true` +
`SameSite=None` so the React UI can iframe panels. Grafana's sqlite lives in `/tmp`; everything
that matters is provisioned from the image, so a cold start rebuilds the identical org.

- Datasource: `provisioning/datasources/clickhouse.yml` → `https://<PUBLIC_HOST>/ch` (Caddy
  strips the `/ch` prefix), protocol `http`, `secure: true`, user `agent_ro`, password from
  Secret Manager (`slateiq-ch-ro-password`).
- Dashboard: `dashboards/slateiq-production-health.json`, uid **`slateiq-prod-health`**, also
  set as the anonymous home dashboard.

**"SlateIQ Production Health"** — 8 panels, `$production` and `$day` variables:
pages planned vs shot per day · schedule position (pages ahead/behind) · shooting ratio by
scene · flags by type per day · takes per hour on the selected shooting day (bucketed by slate
timecode) · wrap-delay trend · circled vs NG donut · scenes-at-risk table.
Sources: `slateiq.daily_progress`, `slateiq.scene_progress`, `slateiq.flag_summary`,
`slateiq.take`.

Deploy is two-pass because `GF_SERVER_ROOT_URL` must be the service's own URL, which only
exists after the first deploy.

### Alternative for a Grafana-track sibling submission (not built)

If SlateIQ were also entered on a Grafana track, the natural addition is
[`grafana/mcp-grafana`](https://github.com/grafana/mcp-grafana) — Grafana's own MCP server —
alongside `mcp-clickhouse` rather than instead of it:

- Run it against a free **Grafana Cloud** stack (free forever: 10k series, 50 GB logs, 3 users)
  or against this same Cloud Run instance, in stdio or SSE mode, with a Grafana service-account
  token scoped to Viewer.
- It exposes `search_dashboards`, `get_dashboard_by_uid`, `query_prometheus`, `list_datasources`,
  `list_alert_rules`, `get_incident` and friends. Attached to the ADK coordinator as a second
  `McpToolset`, the agent gains "which dashboard already answers this?" and "is anything
  alerting?" on top of "write the SQL" — i.e. **mcp-clickhouse writes new analysis,
  mcp-grafana reuses existing analysis**, and the report agent can cite a panel URL instead of
  re-deriving a number.
- The demo story: ask "are we on schedule?", have the agent answer from ClickHouse *and* deep
  link to the live "Production Health" panel that proves it.
- Cost stays $0: Grafana Cloud's free tier plus one more scale-to-zero Cloud Run revision.

Deliberately out of scope for the ClickHouse-track submission — noted here so it is a
half-day of work rather than a redesign.

---

## 5. Clips on GCS

```bash
deploy/gcs/publish_clips.sh
```

Creates `slateiq-media-<project>` (us-central1, standard, uniform access, `allUsers:objectViewer`,
CORS for `GET`/`HEAD`), uploads `data/clips/*.mp4` → `clips/` and `data/thumbs/*.jpg` → `thumbs/`
with `Cache-Control: public, max-age=31536000, immutable`. The two prefixes match the relative
`clip_uri` / `thumb_uri` values stored in ClickHouse, so the UI can build `<base>/<uri>` directly.

Then point the database rows at it:

```bash
python ingest/load.py --replace --base-url https://storage.googleapis.com/slateiq-media-<project>
```

---

## Teardown / cost control

```bash
gcloud compute instances stop slateiq-data --zone us-central1-a   # stops the only non-zero line item
gcloud run services update slateiq --min-instances 0 --region us-central1   # already the default
```

Do **not** delete the VM (deletion protection is on and it holds the demo dataset), and do not
touch the unrelated `ai-magic-design-frontend` / `design-search-api` services in this project.
