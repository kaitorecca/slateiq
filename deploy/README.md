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
        |  bearer token)  |  (agent_ro: SELECT on slateiq.*) | mcp-clickhouse 0.6 (http) |
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
`vm.overcommit_memory=1`, caps container logs, and installs + enables the
`slateiq-stack.service` systemd unit that brings compose up on every boot (see
[Resilience](#resilience--what-brings-the-stack-back)).
The Ops Agent is deliberately **not** installed — it would cost ~120 MB of a 1 GiB box.

`deploy_stack.sh` then:
1. generates `.secrets/deploy.env` (three random secrets) on first run, and refreshes the
   derived `PUBLIC_HOST` / `CLICKHOUSE_MCP_URL` values on every run;
2. tars `deploy/vm/compose/` up to `/opt/slateiq` and writes a 0600 `.env` there;
3. `docker compose up -d --build`;
4. curls `https://<ip>.sslip.io/health`, `/ch/ping`, and an unauthenticated `POST /mcp`
   (which must return **401**).

After it finishes, `deploy/vm/healthcheck.sh` is the one command that proves the whole plane —
see [Health check](#health-check) below.

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
Per-user limits live in `compose/clickhouse/users.d/slateiq.xml`: the `default` (seeding) profile
keeps `max_memory_usage 400 MB` and 200 MB spill thresholds; the `agent_ro` profile is tighter —
see below.

**Users:** `default` (admin, used only by seeding, reachable only on localhost/inside the
container) and **`agent_ro`** — the only identity mcp-clickhouse, the agent and Grafana ever use.
`agent_ro` is least-privileged in three independent layers, all declared in
`compose/clickhouse/users.d/slateiq.xml` so a rebuild reproduces them exactly:

1. **RBAC grants.** Five `GRANT` statements, and nothing else:

   ```
   GRANT SHOW, SELECT ON slateiq.*
   GRANT SELECT ON system.settings     -- clickhouse-connect reads it on every connect
   GRANT SELECT ON system.tables       -- mcp-clickhouse list_tables
   GRANT SELECT ON system.columns      -- mcp-clickhouse list_tables column metadata
   ```

   The three system tables are row-filtered by ClickHouse to objects the user may see, so they
   expose the `slateiq` schema and nothing more. Everything else — `system.query_log`,
   `system.users`, `system.grants`, `system.zookeeper`, the `default` database — is
   **ACCESS_DENIED (code 497)**, not merely read-only. This replaces the legacy
   `<allow_databases>` list, which only filtered `SHOW` output and left the user holding
   ClickHouse's default "everything" grant (including `SYSTEM SHUTDOWN`, `INTROSPECTION` and
   `SOURCES`). `<grants>` and `<allow_databases>` are mutually exclusive, which is why the
   latter is gone.

2. **`readonly=1`** (was `readonly=2`). No writes, no DDL, and — the reason for the change —
   **no table functions at all**: `url()`, `file()`, `remote()`, `s3()`, `mysql()` are refused,
   closing the SSRF / local-file-read class that QC #2 finding **G-2** flagged as depending on a
   setting we did not control. `mcp-clickhouse` detects that the server already enforces
   readonly and echoes `1` back per query rather than trying to set it, so this is a no-op for
   it (see `get_readonly_setting` in `mcp_server.py`).

3. **Resource caps** (settings profile `agent_ro`): `max_execution_time 30`,
   `max_result_rows 20000` / `max_result_bytes 16 MiB` with `result_overflow_mode break`,
   `max_rows_to_read 50M` / `max_bytes_to_read 2 GiB`, `max_memory_usage 300 MB`,
   `max_threads 2`, plus a 240 queries/min quota. A runaway query degrades or errors; it does
   not OOM a 1 GiB box.

   One deliberate exception exists to `readonly=1` freezing every setting: the Grafana
   ClickHouse datasource plugin sends its own `max_execution_time` on each connection handshake
   (`jsonData.queryTimeout` + 4 s) and fails the whole query with code 164 if the server refuses
   it. A `<constraints>` block marks that single setting `changeable_in_readonly` with
   `<max>65</max>`, so a client may move the timeout between 30 s and 65 s and change nothing
   else. `provisioning/datasources/clickhouse.yml` has been lowered to `queryTimeout: 25`
   (→ 29 s), so after the next Grafana image rebuild the real ceiling is the profile's 30 s
   again for every identity.

Changing this file needs no rebuild — ClickHouse hot-reloads `users.d/` within a few seconds.
`docker restart slateiq-mcp` afterwards only refreshes mcp-clickhouse's pooled connections.

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

### Resilience — what brings the stack back

Three layers, deliberately overlapping, because each covers a case the others do not:

| Layer | Where | Covers |
|---|---|---|
| `restart: unless-stopped` on all three services | `compose/docker-compose.yml` | a crashed/OOM-killed container, and a docker daemon restart |
| **`slateiq-stack.service`** (systemd, `Type=oneshot`, `RemainAfterExit=yes`, `After=docker.service network-online.target`) | written and `systemctl enable`d by `bootstrap.sh` | boot, **and** a container that was manually `docker stop`ped — which `unless-stopped` deliberately will not restart. `ExecStartPre` waits up to 60 s for the docker socket, because it can lag systemd on a 1 GiB box. |
| `bootstrap.sh` re-run by GCE as the instance **startup-script** on every boot | `create_vm.sh --metadata-from-file startup-script=` | a boot where the unit file itself is missing (first provision, or a restored disk) |

Both ClickHouse and mcp-clickhouse also carry container `healthcheck`s (`/ping` and `/health`,
15 s / 20 s intervals), and `mcp` has `depends_on: {clickhouse: {condition: service_healthy}}`,
so a cold boot never starts the MCP server against a database that is not accepting queries yet.

Measured on 2026-09-05:

```
docker restart slateiq-mcp   -> /health returns OK again after ~12 s
docker kill    slateiq-mcp   -> back up and healthy inside 30 s (restart policy)
docker stop    slateiq-caddy -> stays down (correct); systemctl restart slateiq-stack -> up in 11 s
sudo systemctl reboot        -> whole stack healthy 103 s after the reboot command,
                                all three containers healthy, ephemeral IP unchanged
```

A `reboot` keeps the ephemeral IP; only `gcloud compute instances stop` releases it.

### Health check

```bash
deploy/vm/healthcheck.sh            # 7 checks, from the laptop, no ssh needed
deploy/vm/healthcheck.sh --ssh      # + containers, RAM and the systemd unit on the VM
deploy/vm/healthcheck.sh --quiet    # exit code only, for a cron or watch loop
```

Exit 0 = all green, 1 = something failed, and every line prints the value it saw. It covers:
MCP `/health`; unauthenticated `POST /mcp` returning **401**; an MCP `initialize` handshake with
the bearer token; ClickHouse `/ch/ping`; **hosted-vs-local row counts** for all seven base tables
(this is what caught `continuity_note` sitting at 0 rows on the VM while local had 66); that
`agent_ro` still gets ACCESS_DENIED on `system.query_log` and on `CREATE TABLE`; and the Cloud Run
agent's `/api/health`. Local ClickHouse being down downgrades the row-count checks to `skip`
rather than failing them.

### Operating

```bash
gcloud compute ssh slateiq-data --zone us-central1-a --command 'cd /opt/slateiq && docker compose ps'
gcloud compute ssh slateiq-data --zone us-central1-a --command 'docker logs --tail 50 slateiq-mcp'
gcloud compute ssh slateiq-data --zone us-central1-a --command 'free -m && docker stats --no-stream'
gcloud compute ssh slateiq-data --zone us-central1-a --command 'systemctl status slateiq-stack.service'
```

To change `agent_ro`'s privileges: edit `compose/clickhouse/users.d/slateiq.xml`, `gcloud compute
scp` it to `/opt/slateiq/clickhouse/users.d/`, wait ~5 s for the hot reload, then
`docker restart slateiq-mcp`. `deploy_stack.sh` does the same thing for the whole bundle.

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

The image is always `agent/Dockerfile` built with the **repo root** as the Cloud Build context
(the agent package imports `db/SCHEMA.md` and serves `web/dist`), via
`deploy/cloudrun/cloudbuild.agent.yaml`. The script exits early if that Dockerfile is missing.

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
  strips the `/ch` prefix), protocol `http`, `secure: true`, user `agent_ro` (`readonly=1`,
  `GRANT SELECT ON slateiq.*` only), `queryTimeout: 25`, password from Secret Manager
  (`slateiq-ch-ro-password`). Do not raise `queryTimeout` past 61 — the plugin sends
  `queryTimeout + 4` as `max_execution_time` and the server caps that setting at 65.
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
