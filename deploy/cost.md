# Why SlateIQ's hosting bill is $0

Hard constraint: **no new cost — Google Cloud Always Free tier or existing credits only.**
Every hosted piece below is sized to sit inside a permanent free allowance, not a trial.

| Piece | What we run | Free allowance | Our usage | Cost |
|---|---|---|---|---|
| **Compute Engine** | 1x `e2-micro` (`slateiq-data`, us-central1-a) running ClickHouse + mcp-clickhouse + Caddy | 1x e2-micro/month in us-west1 / **us-central1** / us-east1 | exactly 1, never a second | **$0** |
| **Persistent disk** | 30 GB `pd-standard` boot disk | 30 GB-months standard PD | exactly 30 GB | **$0** |
| **Cloud Run (agent)** | `slateiq`, min-instances **0**, max 2, 1 vCPU / 1 GiB, concurrency 40 | 2M requests, 180k vCPU-s, 360k GiB-s, 1 GiB egress NA / month | a demo's worth of requests; **zero idle cost because it scales to zero** | **$0** |
| **Cloud Run (Grafana)** | `slateiq-grafana`, min 0, max 1, 1 vCPU / 512 MiB | same pool as above | dashboard views only | **$0** |
| **Artifact Registry** | repo `slateiq` (2 images) | 0.5 GB storage | ~400 MB, with a cleanup policy deleting untagged images after 7d and keeping 5 versions | **$0** |
| **Cloud Build** | image builds | 120 build-minutes/day | a handful of ~3 min builds | **$0** |
| **Secret Manager** | `slateiq-google-api-key`, `slateiq-ch-ro-password` | 6 active secret versions, 10k access ops/month | 2 secrets x **1** active version each (deploy scripts destroy superseded versions) | **$0** |
| **Cloud Storage** | bucket `slateiq-media-<project>`, standard, us-central1 | 5 GB-months, 5k class-A + 50k class-B ops, 100 GB egress | < 1 GB of clips/thumbs, `max-age=31536000` so replays are cache hits | **$0** |
| **Network egress** | VM -> internet | 1 GB/month from North America | MCP responses are small JSON; media is served from GCS, not the VM | **$0** |
| **TLS certificates** | Let's Encrypt via Caddy, hostname `<ip>.sslip.io` | free | no domain purchase, no Cloud DNS zone, no managed cert | **$0** |
| **Gemini** | `gemini-3.5-flash` / `3.1-flash-lite` via the Gemini API key | existing free quota / credits | all results cached to `data/cache/`, so re-runs cost nothing; < 15 min of video analysed total | **$0** |

## Deliberate omissions (each would have cost money)

- **No Cloud SQL / BigQuery / Bigtable** — ClickHouse on the free VM is the analytical store.
- **No GKE, no Vertex Agent Engine** — ADK runs as an ordinary FastAPI container on Cloud Run.
- **No Cloud Logging/Monitoring agent on the VM** — the Ops Agent is explicitly *not* installed
  (`google-logging-enabled=false`, `google-monitoring-enabled=false`). It would eat ~120 MB of a
  1 GiB box and push log ingest toward the 50 GB free ceiling. Serial-port logging (free) covers boot.
- **No Cloud NAT, no load balancer, no Cloud Armor** — Caddy on the VM terminates TLS directly.
- **No static IP reservation, no Cloud DNS zone** — sslip.io maps the IP into a hostname for free.
- **No Cloud Run min-instances > 0** — a warm instance is the single easiest way to accidentally
  spend money on Cloud Run. Cold start for the agent is ~3-5 s, acceptable for a demo.

## The one real caveat: the external IPv4 address

Since 2020 Google charges for **all** external IPv4 addresses attached to a VM, including
ephemeral ones — about **$0.0035/hour ≈ $2.50/month** — and this is *not* part of the Always Free
tier (the free e2-micro covers the instance, not its IP). This is the only line item on the whole
project that can be non-zero.

Mitigations, in order of preference:

1. **Free-trial / existing credits absorb it.** ~$2.50/month against the project's credit balance.
2. **Ephemeral, not static.** `create_vm.sh` deliberately does *not* reserve a static IP. An
   ephemeral IP is released when the instance stops, so `gcloud compute instances stop slateiq-data`
   between demo sessions stops the charge entirely (the instance itself is free either way).
   Cost of that: the IP changes on restart, so `PUBLIC_HOST` (`<ip>.sslip.io`) changes with it —
   re-run `deploy/vm/deploy_stack.sh` (rewrites `.secrets/deploy.env`, re-issues the cert) and
   `deploy/cloudrun/deploy_agent.sh` to re-point the agent. Both are idempotent, ~4 minutes total.
3. **After the hackathon**, `gcloud compute instances stop slateiq-data` (do not delete — the VM
   has deletion protection on and holds the demo dataset).

Total worst case if credits do not apply: **~$2.50/month**, and $0 while the VM is stopped.

## Guardrails we put in place

- `--deletion-protection` on the VM, so no script can accidentally destroy the dataset.
- Artifact Registry cleanup policy (untagged > 7d deleted, 5 versions kept) to stay under 0.5 GB.
- ClickHouse system logs mostly disabled and `query_log` TTL'd to 3 days — bounded disk on a
  30 GB volume that must never need growing (a bigger disk is a billable disk).
- Docker `json-file` logs capped at 10 MB x 2 per container, plus a weekly image prune.
- `max-instances` set on both Cloud Run services so a runaway loop cannot scale into real money.

To watch it: `gcloud billing budgets list` — set a $1 budget alert on the billing account if one
does not exist yet.
