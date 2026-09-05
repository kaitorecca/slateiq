# deploy/OUTPUT.md — live SlateIQ endpoints

Last verified: **2026-09-05 ~16:40 UTC** (revision `slateiq-00007-jnp`) · project `gke-hackathon-472816` · region `us-central1`

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
CLICKHOUSE_USER=agent_ro
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
| Artifact Registry | `slateiq` (us-central1) — images `slateiq`, `grafana` |
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
| `continuity_note` | 66 |
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

Containers: `slateiq-ch` (healthy), `slateiq-mcp` (healthy), `slateiq-caddy` — all `unless-stopped`.

## Known caveats

- **The VM's external IP is ephemeral.** If the instance is stopped/restarted the IP changes and
  with it `PUBLIC_HOST` (`<ip>.sslip.io`). Recovery: `deploy/vm/deploy_stack.sh`, then
  `deploy/cloudrun/deploy_agent.sh` and `deploy/grafana/deploy.sh` (~4 min, all idempotent).
  This is also the only line item that can cost money — see [cost.md](cost.md).
- Grafana's sqlite is in `/tmp`, so anything a viewer changes in the UI is lost on the next cold
  start. That is intentional: the image is the source of truth.
