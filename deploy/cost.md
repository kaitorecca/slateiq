# Why SlateIQ's hosting bill is $0

Hard constraint: **no new cost — Google Cloud Always Free tier or existing credits only.**
Every hosted piece below is sized to sit inside a permanent free allowance, not a trial.

| Piece | What we run | Free allowance | Our usage | Cost |
|---|---|---|---|---|
| **Compute Engine** | 1x `e2-micro` (`slateiq-data`, us-central1-a) running ClickHouse + mcp-clickhouse + Caddy | 1x e2-micro/month in us-west1 / **us-central1** / us-east1 | exactly 1, never a second | **$0** |
| **Persistent disk** | 30 GB `pd-standard` boot disk | 30 GB-months standard PD | exactly 30 GB | **$0** |
| **Cloud Run (agent)** | `slateiq`, min-instances **0**, max 2, 1 vCPU / 1 GiB, concurrency 40 | 2M requests, 180k vCPU-s, 360k GiB-s, 1 GiB egress NA / month | a demo's worth of requests; **zero idle cost because it scales to zero** | **$0** |
| **Cloud Run (Grafana)** | `slateiq-grafana`, min 0, max 1, 1 vCPU / 512 MiB | same pool as above | dashboard views only | **$0** |
| **Artifact Registry** | repo `slateiq` (packages `slateiq`, `grafana`) | 0.5 GB storage / month | **~0.4 GB** after the 2026-09-05 cleanup (see below) | **$0**–$0.04 |
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
- Artifact Registry cleanup policy, `deploy/cloudrun/ar-cleanup-policy.json`, applied to the
  `slateiq` repo: untagged versions deleted after 1 day, tagged versions after 7 days, most
  recent 3 versions per package always kept. **This document previously claimed such a policy
  existed; it did not** — `gcloud artifacts repositories describe slateiq` returned
  `cleanupPolicies: null` and the repo had grown to **657 MB**, past the 0.5 GB free
  allowance. Fixed on 2026-09-05: policy applied with `--no-dry-run`, and the three oldest
  `slateiq` image digests (not referenced by any Cloud Run revision) deleted by hand, bringing
  the repo to 5 versions / ~0.4 GB. Re-check with
  `gcloud artifacts repositories list --location us-central1 --format='table(name,sizeBytes)'`
  (the size metric is recomputed daily, so it lags a deletion by up to 24 h).
- ClickHouse system logs mostly disabled and `query_log` TTL'd to 3 days — bounded disk on a
  30 GB volume that must never need growing (a bigger disk is a billable disk).
- Docker `json-file` logs capped at 10 MB x 2 per container, plus a weekly image prune.
- `max-instances` set on both Cloud Run services so a runaway loop cannot scale into real money.
- `agent_ro` holds `GRANT SELECT ON slateiq.*` and three system tables, `readonly=1`, a 30 s
  `max_execution_time`, a 20 000-row result cap, a 300 MB memory cap and a 240 queries/minute
  quota. Cost-relevant because the VM has no autoscaling to hide behind: an unbounded agent
  query is a 1 GiB OOM, and an OOM is a demo outage, not a bill — but the read caps also stop a
  runaway loop burning the VM's 1 GB/month free egress allowance.

## Current-month estimate (September 2026, as of 2026-09-05 07:45 UTC)

| Line item | Rate | Month-to-date | If left running to 30 Sep |
|---|---|---|---|
| Ephemeral external IPv4 on `slateiq-data` (up since 2026-09-04 20:44 PDT) | $0.0035/h | ~4 h → **$0.015** | ~627 h → **$2.19** |
| e2-micro instance (us-central1-a) | Always Free (1/month) | $0 | $0 |
| 30 GB pd-standard boot disk | Always Free (30 GB-months) | $0 | $0 |
| Cloud Run `slateiq` + `slateiq-grafana`, both min-instances **0** | free tier (2M req, 180k vCPU-s, 360k GiB-s) | $0 | $0 |
| Artifact Registry, repo `slateiq` ~0.4 GB | 0.5 GB free, then $0.10/GB-month | $0 (inside free tier) | $0, or ~$0.04 if the pre-existing `cloud-run-source-deploy` repo (1.55 GB, **not ours** — it belongs to `ai-magic-design-frontend` / `design-search-api`) has already consumed the project's free allowance |
| Cloud Storage `slateiq-media-*`, 43.7 MB | 5 GB free | $0 | $0 |
| Secret Manager, 2 secrets × 1 enabled version | 6 free versions | $0 | $0 |
| Cloud Build, Gemini, Let's Encrypt, sslip.io | free / cached / no-cost | $0 | $0 |
| **Total** | | **≈ $0.02** | **≈ $2.19** (worst case, no credits) |

Realistic figure: the demo ends at the 9 Sep 14:00 PDT deadline and the VM is stopped there, so
the IP runs ~113 h → **≈ $0.40** for the whole project, before credits.

Verified on 2026-09-05:

```
$ gcloud compute instances describe slateiq-data --zone us-central1-a     --format='value(machineType,deletionProtection,status)'
.../machineTypes/e2-micro   True   RUNNING
$ gcloud compute disks describe slateiq-data --zone us-central1-a --format='value(type,sizeGb)'
.../diskTypes/pd-standard   30
$ gcloud run services describe slateiq --region us-central1     --format='value(spec.template.metadata.annotations)' | tr ';' '\n' | grep -i scale
autoscaling.knative.dev/maxScale=2        # no minScale annotation => min-instances 0
$ ... slateiq-grafana ...
autoscaling.knative.dev/maxScale=1        # ditto
$ gcloud compute addresses list
(empty)                                   # no static IP reserved anywhere
$ gcloud storage du -s gs://slateiq-media-gke-hackathon-472816
43659466                                  # 43.7 MB of 5 GB
```

To watch it: a **$10/month budget alert with 50/90/100/150% thresholds already exists** on
billing account `018053-F3C7B5-7FC636` (`gcloud billing budgets list
--billing-account=018053-F3C7B5-7FC636`), alongside a second "Warning Extreme" $12 budget. At an
expected ≈$2.19/month worst case there is a 4× margin before the first alert fires.

### Added 5 Sep — still $0
| Item | Free tier | Our usage |
|---|---|---|
| Cloud Scheduler `slateiq-keepwarm` | 3 jobs/month free | 1 job, 288 runs/day |
| Cloud Monitoring uptime check + alert + email channel | uptime checks & alerting free; 1M external checks/month | 1 check × 3 regions / 15 min ≈ 8.6k/month |
| Cloud Run requests from the ping | 2M req/month free; CPU billed only during the ~30 ms request | ≈ 8.6k req/month |
