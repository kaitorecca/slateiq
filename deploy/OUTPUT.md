# deploy/OUTPUT.md — live SlateIQ endpoints

Last verified: **2026-09-05 ~16:40 UTC** (revision `slateiq-00007-jnp`) · project `gke-hackathon-472816` · region `us-central1`
Data plane re-verified after the least-privilege / resilience hardening: **2026-09-05 07:45 UTC** — see [Security](#security--agent_ro-least-privilege).

Secrets referenced below live in `.secrets/deploy.env` (gitignored). Nothing here is a secret.

## Endpoints

| What | URL |
|---|---|
| **Agent + UI (Cloud Run)** | https://slateiq-957930801789.us-central1.run.app  (alias: `https://slateiq-hbissixc2q-uc.a.run.app`) |
| **Grafana** | https://slateiq-grafana-hbissixc2q-uc.a.run.app |
| **Production Health dashboard** | https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health |
| **ClickHouse MCP (official server)** | `https://35.239.36.85.sslip.io/mcp` |
| **MCP health (no auth)** | https://35.239.36.85.sslip.io/health |
| **ClickHouse HTTP (read-only)** | `https://35.239.36.85.sslip.io/ch/` (path-mounted, for Grafana) |
| **ClickHouse HTTP at root** | `https://35.239.36.85.sslip.io:8443/` (for clickhouse-connect / clickhouse-client) |
| **Clips / thumbnails (GCS)** | `https://storage.googleapis.com/slateiq-media-gke-hackathon-472816` |

## Environment for the agent

```bash
CLICKHOUSE_MCP_URL=https://35.239.36.85.sslip.io/mcp
CLICKHOUSE_MCP_TOKEN=<.secrets/deploy.env: CLICKHOUSE_MCP_TOKEN>   # sent as: Authorization: Bearer <token>
# Media. When set, the server rewrites relative clip_uri/thumb_uri ("clips/x.mp4") to absolute
# GCS URLs in /api/takes, /api/take/{id}/events and the take enrichment that runs before the
# `final` SSE event. Unset = local behaviour (files served from /clips and /thumbs).
CLIPS_BASE_URL=https://storage.googleapis.com/slateiq-media-gke-hackathon-472816

# Served to the browser by GET /api/config. web/ is a static Vite build, so VITE_* is frozen at
# build time; this is the only path by which server config reaches the SPA.
APP_URL=https://slateiq-957930801789.us-central1.run.app
GRAFANA_URL=https://slateiq-grafana-hbissixc2q-uc.a.run.app
GRAFANA_DASH_UID=slateiq-prod-health
GRAFANA_PANELS=2:Schedule position,1:Pages planned vs shot per day,3:Print ratio (takes per circled take) by scene,8:Scenes at risk
REPO_URL=https://github.com/kaitorecca/slateiq

# Direct read-only ClickHouse — UI takes-gallery passthrough ONLY, never agent reasoning.
CLICKHOUSE_HOST=35.239.36.85.sslip.io
CLICKHOUSE_PORT=8443
CLICKHOUSE_SECURE=true
CLICKHOUSE_USER=agent_ro          # readonly=1, GRANT SELECT ON slateiq.* only — see Security below
CLICKHOUSE_PASSWORD=<.secrets/deploy.env: CH_AGENT_RO_PASSWORD>
CLICKHOUSE_DATABASE=slateiq
```

Frontend build: `VITE_APP_URL=https://slateiq-957930801789.us-central1.run.app`.

MCP transport is **streamable HTTP** (`mcp-clickhouse` 0.6.0). Requests must send
`Accept: application/json, text/event-stream`. Unauthenticated requests get **401**.

## Resources created (nothing pre-existing was touched)

| Resource | Name |
|---|---|
| Compute Engine VM | `slateiq-data` (e2-micro, us-central1-a, 30 GB pd-standard, deletion protection ON) |
| Firewall rule | `slateiq-allow-web` (tcp 80/443/8443 + udp 443, target tag `slateiq-data`) |
| Cloud Run | `slateiq` (agent), `slateiq-grafana` |
| Artifact Registry | `slateiq` (us-central1) — packages `slateiq`, `grafana`; cleanup policy from `deploy/cloudrun/ar-cleanup-policy.json` |
| Secret Manager | `slateiq-google-api-key`, `slateiq-ch-ro-password` (1 active version each) |
| GCS bucket | `slateiq-media-gke-hackathon-472816` (public read, 48 objects, 43.7 MB) |
| Runtime service account | `slateiq-dev@gke-hackathon-472816.iam.gserviceaccount.com` |

The project's Compute Engine default service account does not exist, so both Cloud Build and
Cloud Run are pinned to `slateiq-dev@` explicitly (`--service-account`,
`--default-buckets-behavior=REGIONAL_USER_OWNED_BUCKET`).

Untouched, as instructed: `ai-magic-design-frontend`, `design-search-api`.

## Verification transcript

```
$ curl -s https://35.239.36.85.sslip.io/health
OK

$ curl -s https://35.239.36.85.sslip.io/ch/ping
Ok.

$ curl -s -o /dev/null -w '%{http_code}\n' -X POST https://35.239.36.85.sslip.io/mcp
401

$ curl -s https://35.239.36.85.sslip.io/mcp -H "Authorization: Bearer $T" \
    -H 'Accept: application/json, text/event-stream' -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}'
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18",...,
       "serverInfo":{"name":"mcp-clickhouse","version":"0.6.0"}}}

$ curl -s 'https://35.239.36.85.sslip.io/ch?query=SELECT+count()+FROM+slateiq.take' --user agent_ro:***
2503

$ curl -s https://slateiq-grafana-hbissixc2q-uc.a.run.app/api/health
{"database":"ok","version":"12.4.3","commit":"86c83248"}

$ curl -s -X POST .../api/ds/query -d '{... "rawSql":"SELECT scene_number, round(print_ratio,2) ..."}'
{"results":{"A":{"status":200,"frames":[{... "values":[["98","19","91"],[7.55,7.18,6.71]]}]}}}

$ curl -s https://slateiq-957930801789.us-central1.run.app/api/health
{"status":"ok","ok":true,"mcp":"up","clickhouse":"up","model":"gemini-3.5-flash",
 "clickhouse_mcp_url":"https://35.239.36.85.sslip.io/mcp","clickhouse_mcp_auth":true,
 "database":"slateiq","schema_source":"/app/db/SCHEMA.md","web_dist":true,"clips_dir":true}

$ curl -N -X POST .../api/chat -d '{"message":"How many takes were shot on day 12, and how many were circled?"}'
event: agent   {"name":"production_agent"}
event: tool_call   {"name":"run_query","args":{"query":"SELECT day_number, takes, circled FROM slateiq.daily_progress WHERE day_number = 12 LIMIT 1"}}
event: tool_result {"rows":1,"summary":"[[12, 175, 38]]"}
event: final   "On Day 12, we shot a total of **175 takes**, of which **38 were circled** ...
                print ratio of **4.6:1** ..."
   -> the SQL was written by the agent and executed through mcp-clickhouse on the VM.

$ curl -sI https://storage.googleapis.com/slateiq-media-gke-hackathon-472816/clips/TOS-D12-S12-A-01-A.mp4
HTTP/2 200 · content-type: video/mp4 · cache-control: public, max-age=31536000, immutable
```

### Hosted media + runtime config (re-verified 16:40 UTC, revision `slateiq-00007-jnp`)

```
$ curl -s .../api/config
{"app_url":"https://slateiq-957930801789.us-central1.run.app",
 "grafana_url":"https://slateiq-grafana-hbissixc2q-uc.a.run.app",
 "grafana_dash_uid":"slateiq-prod-health",
 "grafana_panels":[{"id":"2","title":"Schedule position"},
                   {"id":"1","title":"Pages planned vs shot per day"},
                   {"id":"3","title":"Print ratio (takes per circled take) by scene"},
                   {"id":"8","title":"Scenes at risk"}],
 "mcp_health_url":"https://35.239.36.85.sslip.io/health",
 "repo_url":"https://github.com/kaitorecca/slateiq",
 "clips_base_url":"https://storage.googleapis.com/slateiq-media-gke-hackathon-472816"}

$ curl -s '.../api/takes?scene=27&limit=3'   # media URLs are absolute, not "clips/x.mp4"
TOS-D12-S27-A-01-A | https://storage.googleapis.com/slateiq-media-.../clips/TOS-D12-S27-A-01-A.mp4
                   | https://storage.googleapis.com/slateiq-media-.../thumbs/TOS-D12-S27-A-01-A.jpg

$ curl -sI <that clip>   -> HTTP/2 200 · video/mp4  · 1,620,774 B · access-control-allow-origin: *
$ curl -sI <that thumb>  -> HTTP/2 200 · image/jpeg ·    11,529 B
$ curl -sI .../thumbs/TOS-D12-S27-A-01-A.jpg  -> HTTP/2 200 · image/jpeg (baked into the image too)
$ curl -s -o /dev/null -w '%{http_code} %{content_type}' .../thumbs/nope.jpg  -> 404 application/json
   (was 200 text/html — the SPA catch-all used to swallow every missing poster)

$ curl -s -o /dev/null -w '%{time_total}' '.../api/report/dpr?day=12'   -> 0.67 s  (was ~200 s)
```

Browser check on the hosted URL at 1440×900 (Chrome DevTools): Takes shows **24/24 posters loaded**
and a clip plays inline (`currentSrc` = the GCS URL, 1280×534, `readyState 4`); Production Health
renders **4 live Grafana `d-solo` iframes**; **0 console errors**.

### Cold start

`min-instances` stays **0** (an idle instance is the one thing that would cost money). Measured
from the Cloud Run logs, `Starting new instance` → `Application startup complete` = **15.7 s**,
which is the ADK import, not ClickHouse. Warm: **~0.6 s** for `/` and `/api/health`. Documented in
the README instead of papered over with a warm-up cron.

## Hosted data (seeded from local ClickHouse, exact row-count match)

| Table | Rows |
|---|---|
| `production` | 1 |
| `scene` | 120 |
| `shooting_day` | 30 |
| `take` | 2,503 |
| `take_analysis` | 2,503 |
| `take_event` | 26,750 |
| `continuity_note` | 66 (was 0 on the VM until re-seeded 2026-09-05 — see Security) |
| **`frame_telemetry`** | **3,074,957** |
| `take_daily_agg` (MV) | 12 |
| `take_scene_agg` (MV) | 51 |

Views `daily_progress`, `scene_progress` (with the renamed `print_ratio` column), `flag_summary`
are present. Total on disk: **53.5 MiB** — `frame_telemetry` moved in 8 hash-modulo chunks of
~400k rows, ~9 MB of zstd Parquet each, so the 1 GiB VM never saw more than one chunk at a time.

## Health / RAM on the VM

```
$ free -m
               total        used        free       buff/cache   available
Mem:             969         684         128              296         285
Swap:           2047         113        1934
```

Containers: `slateiq-ch` (healthy), `slateiq-mcp` (healthy), `slateiq-caddy` — all
`unless-stopped`, and brought up on boot by the `slateiq-stack.service` systemd unit.
`deploy/vm/healthcheck.sh` verifies the whole plane from the laptop in one command.

---

## Security — `agent_ro` least privilege

Hardened 2026-09-05, 07:25–07:45 UTC.

`agent_ro` is the only database identity reachable from the internet: mcp-clickhouse (and so the
ADK agent), Grafana's datasource, and the UI's takes-gallery passthrough all use it. It is now
scoped by RBAC grants rather than by ClickHouse's legacy `<allow_databases>` list, which
[QC #2 §2 finding G-1](../docs/QC_2_AGENT.md) called out: `readonly=1` blocks writes, not reads,
so `system.query_log` and `system.users` were fully readable through the chat box.

**Before** — `SHOW GRANTS FOR agent_ro` returned ClickHouse's default "everything" grant:

```
GRANT CREATE ARBITRARY TEMPORARY TABLE, CREATE FUNCTION, ..., KILL QUERY,
      SYSTEM SHUTDOWN, ..., displaySecretsInShowAndSelect, INTROSPECTION, SOURCES,
      CLUSTER ON *.* TO agent_ro
GRANT TABLE ENGINE ON * TO agent_ro
GRANT CHECK, SHOW, SELECT, INSERT, ALTER, CREATE DATABASE, CREATE TABLE, DROP TABLE, TRUNCATE,
      ... ON slateiq.* TO agent_ro                 (and the same on default.*, INFORMATION_SCHEMA.*)
$ SELECT count() FROM system.query_log             -> 6320
```

`allow_databases` only ever filtered `SHOW` output; the grants underneath were unrestricted, and
`readonly=2` was the only thing preventing a write.

**After** — declared in `deploy/vm/compose/clickhouse/users.d/slateiq.xml`, so `deploy_stack.sh`
reproduces it on a rebuild:

```
$ docker exec slateiq-ch clickhouse-client --user default ... --query 'SHOW GRANTS FOR agent_ro'
GRANT SHOW, SELECT ON slateiq.* TO agent_ro
GRANT SELECT ON system.columns TO agent_ro
GRANT SELECT ON system.settings TO agent_ro
GRANT SELECT ON system.tables TO agent_ro
```

Those three system tables are the structural minimum and nothing more: clickhouse-connect issues
`SELECT name, value, readonly FROM system.settings` on **every** connect (without it no client can
be constructed at all), and mcp-clickhouse's `list_tables` reads `system.tables` + `system.columns`.
ClickHouse row-filters all three by access rights, so they leak only the `slateiq` schema —
`SELECT database, count() FROM system.tables GROUP BY database` returns `slateiq 15` / `system 3`.

### Verification transcript

Session settings actually in force:

```
$ SELECT currentUser(), getSetting('readonly'), getSetting('max_execution_time'),
         getSetting('max_memory_usage'), getSetting('max_result_rows')
agent_ro   1   30   314572800   20000
```

Through the hosted MCP endpoint — a raw `mcp` streamable-HTTP client from `.venv`, against
`https://35.239.36.85.sslip.io/mcp` with the bearer token:

```
server: mcp-clickhouse 0.6.0
tools:  ['list_databases', 'list_tables', 'run_query']
list_tables(database="slateiq") -> 39 954 bytes, all 15 objects with full column metadata

Q: SELECT count() FROM slateiq.take
-> {"columns": ["count()"], "rows": [[2503]]}

Q: SELECT day_number, takes, circled FROM slateiq.daily_progress ORDER BY day_number LIMIT 3
-> {"columns": ["day_number","takes","circled"], "rows": [[1,240,52],[2,246,49],[3,284,55]]}

Q: SELECT * FROM system.query_log LIMIT 1
-> Code: 497. DB::Exception: agent_ro: Not enough privileges. ... ON system.query_log. (ACCESS_DENIED)

Q: SELECT name FROM system.users
-> Code: 497. DB::Exception: ... SELECT(name) ON system.users. (ACCESS_DENIED)

Q: SELECT * FROM url('http://169.254.169.254/latest/meta-data/','LineAsString')
-> Code: 497. DB::Exception: ... CREATE TEMPORARY TABLE, URL ON *.*. (ACCESS_DENIED)
```

Directly against ClickHouse on the VM:

```
$ SELECT count() FROM slateiq.take                       -> 2503
$ SHOW DATABASES                                         -> slateiq, system
$ SHOW TABLES FROM slateiq                               -> continuity_note, daily_progress, ...
$ SELECT * FROM file('/etc/passwd','LineAsString')       -> 497 ... FILE ON *.*. (ACCESS_DENIED)
$ INSERT INTO slateiq.take (take_id) VALUES ('x')        -> 497 ... INSERT(take_id) ON slateiq.take
$ CREATE TABLE slateiq.hc_probe(x Int8) ENGINE=Memory    -> 497 ACCESS_DENIED
```

`readonly=1` is what removes the table functions entirely (QC #2 finding **G-2**): under
`readonly=2` they were rejected only because ClickHouse happens to refuse them, and the guardrail
in `agent/` was the only thing we controlled. Settings are frozen with it:

```
$ .../ch?query=SELECT+1&max_memory_usage=999999999  -> Code: 164 Cannot modify ... in readonly mode
$ .../ch?query=SELECT+1&readonly=0                  -> Code: 164 Cannot modify 'readonly' ...
$ .../ch?query=SELECT+1&max_execution_time=65       -> 1        (the one whitelisted setting)
$ .../ch?query=SELECT+1&max_execution_time=66       -> Code: 452 shouldn't be greater than 65
```

The single `changeable_in_readonly` exception exists because the Grafana ClickHouse plugin
(`clickhouse-datasource 4.21.2` / `clickhouse-go 2.47.0`) sends `max_execution_time = queryTimeout
+ 4` on every connection handshake and fails the query with code 164 if the server refuses it —
observed as `64` in `system.query_log`. With the constraint in place the live dashboard query is
green again:

```
$ curl -X POST $GRAFANA/api/ds/query -d '{... "rawSql":"SELECT scene_number, round(print_ratio,2) ..."}'
{"results":{"A":{"status":200,"frames":[{... "values":[["98","19","91"],[7.55,7.18,6.71]]}]}}}
```

`deploy/grafana/provisioning/datasources/clickhouse.yml` has been lowered to `queryTimeout: 25`
so the next Grafana image build lands at 29 s, inside the profile's 30 s default.

Nothing downstream regressed: `/api/health` still reports `"mcp":"up","clickhouse":"up"`, and
`/api/takes` (direct clickhouse-connect on :8443) still returns rows.

### Resilience

| Check | Result |
|---|---|
| `restart: unless-stopped` on all three services | present in `compose/docker-compose.yml` |
| ClickHouse healthcheck | `wget -q -O - http://127.0.0.1:8123/ping \| grep -q Ok`, 15 s / 20 retries / 60 s start period; `mcp` waits on `condition: service_healthy` |
| mcp-clickhouse healthcheck | `GET /health` every 20 s |
| Boot | `slateiq-stack.service` — `systemctl is-enabled` → **enabled**, `is-active` → **active** |
| `docker restart slateiq-mcp` | `/health` back to `OK` after **~12 s**; `run_query` correct immediately after |
| `docker kill slateiq-mcp` | back up and **healthy** within 30 s |
| `docker stop slateiq-caddy` | stays down (correct — `unless-stopped` honours a manual stop); `systemctl restart slateiq-stack` → up in **11 s** |
| **`sudo systemctl reboot`** | whole stack healthy **103 s** after the reboot command; `uptime` 1 min, unit `active`, all three containers healthy, **ephemeral IP unchanged** (`35.239.36.85`) |

`deploy/vm/healthcheck.sh --ssh` — all green, run from the laptop:

```
1. MCP /health           ok  https://35.239.36.85.sslip.io/health -> OK
2. MCP auth              ok  unauthenticated POST /mcp -> 401
3. MCP handshake         ok  initialize -> "name":"mcp-clickhouse","version":"0.6.0"
4. ClickHouse /ch/ping   ok  -> Ok.
5. Row counts (hosted vs local)
   ok  slateiq.take            hosted=2503     == local=2503
   ok  slateiq.take_event      hosted=26750    == local=26750
   ok  slateiq.take_analysis   hosted=2503     == local=2503
   ok  slateiq.scene           hosted=120      == local=120
   ok  slateiq.shooting_day    hosted=30       == local=30
   ok  slateiq.continuity_note hosted=66       == local=66
   ok  slateiq.frame_telemetry hosted=3074957  == local=3074957
6. agent_ro least privilege
   ok  SELECT FROM system.query_log -> ACCESS_DENIED (code 497)
   ok  CREATE TABLE                 -> refused (Code: 497)
7. Cloud Run agent       ok  /api/health -> mcp up, clickhouse up
8. VM (ssh)              slateiq-caddy/ch/mcp all Up, ch+mcp healthy; slateiq-stack enabled+active
ALL CHECKS PASSED
```

**The row-count check earned its keep on the first run:** hosted `slateiq.continuity_note` was
**0 rows** against 66 locally — this document had claimed 66 since the original seed. Re-seeded
with `deploy/vm/seed_remote.sh continuity_note`; now 66/66. Nothing else had drifted.

### Cost guard (re-confirmed 2026-09-05)

```
e2-micro / deletionProtection=True / RUNNING · pd-standard 30 GB
slateiq         maxScale=2, no minScale annotation  -> min-instances 0
slateiq-grafana maxScale=1, no minScale annotation  -> min-instances 0
gcloud compute addresses list  -> (empty)           -> no static IP reserved
secrets: 1 enabled version each · GCS 43.7 MB of 5 GB
```

One real finding: Artifact Registry repo `slateiq` had grown to **657 MB**, over the 0.5 GB free
allowance, and **no cleanup policy existed** despite `cost.md` claiming one did. Fixed —
`deploy/cloudrun/ar-cleanup-policy.json` applied with `--no-dry-run` (untagged > 1 d, tagged > 7 d,
3 most recent versions per package always kept), plus a manual delete of the three oldest `slateiq`
digests that no Cloud Run revision references. Now 5 versions, ~0.4 GB. The 1.55 GB
`cloud-run-source-deploy` repo is **not ours** — it holds `ai-magic-design-frontend` and
`design-search-api` — and was left alone. Current-month estimate is in [cost.md](cost.md):
**≈ $0.02 to date, ≈ $2.19** if the VM's ephemeral IPv4 runs to 30 September.

## Known caveats

- **The VM's external IP is ephemeral.** If the instance is stopped/restarted the IP changes and
  with it `PUBLIC_HOST` (`<ip>.sslip.io`). Recovery: `deploy/vm/deploy_stack.sh`, then
  `deploy/cloudrun/deploy_agent.sh` and `deploy/grafana/deploy.sh` (~4 min, all idempotent).
  This is also the only line item that can cost money — see [cost.md](cost.md).
- Grafana's sqlite is in `/tmp`, so anything a viewer changes in the UI is lost on the next cold
  start. That is intentional: the image is the source of truth.
