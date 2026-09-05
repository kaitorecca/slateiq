/**
 * Build-time configuration for the About page's "Live" section and for the
 * media-availability check in the takes gallery.
 *
 * Every value is a Vite build-time env var (`VITE_*`), inlined at build time.
 * The fallbacks are the endpoints recorded in `deploy/OUTPUT.md`; override them
 * at build time when the stack is redeployed (the VM's external IP is
 * ephemeral, so `VITE_MCP_HEALTH_URL` in particular can move).
 */

const env = import.meta.env

const clean = (v: string | undefined, fallback: string): string =>
  (v && v.trim() ? v.trim() : fallback).replace(/\/+$/, '')

/** Public source. */
export const REPO_URL = 'https://github.com/kaitorecca/slateiq'

/** The hosted SlateIQ agent + UI (Cloud Run, min-instances 0). */
export const APP_URL = clean(env.VITE_APP_URL, 'https://slateiq-957930801789.us-central1.run.app')

/** Grafana on Cloud Run — the Production Health dashboard. */
export const GRAFANA_URL = clean(env.VITE_GRAFANA_URL, 'https://slateiq-grafana-hbissixc2q-uc.a.run.app')

/** Unauthenticated health route of the official mcp-clickhouse server on the VM. */
export const MCP_HEALTH_URL = clean(env.VITE_MCP_HEALTH_URL, 'https://35.239.36.85.sslip.io/health')

/**
 * GCS buckets whose objects are public-read, so a `gs://` clip_uri can be
 * rewritten to an https URL that actually plays. Anything else (the synthetic
 * `gs://slateiq-dailies/...` placeholders) renders a "media not published"
 * card instead of a broken player.
 */
export const PUBLIC_MEDIA_BUCKETS: string[] = (
  env.VITE_PUBLIC_MEDIA_BUCKETS ?? 'slateiq-media-gke-hackathon-472816'
)
  .split(',')
  .map((b) => b.trim())
  .filter(Boolean)

/** Scenes that have real Tears of Steel footage ingested (the rest are synthetic). */
export const FOOTAGE_SCENES: string[] = (
  env.VITE_FOOTAGE_SCENES ?? '12,14A,27,33,41,56,78,102'
)
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

/** How SlateIQ meets the hackathon's Stage-1 requirements. */
export const COMPLIANCE: Array<[string, string]> = [
  ['Gemini 3.5 Flash', 'Every take is watched and structured by Gemini; the agents reason on Gemini too. No non-Google model is used in the product.'],
  ['Google Cloud Agent Builder (ADK)', 'A coordinator plus four specialist sub-agents — editor, production, continuity, report — routed live and visible in the trace panel.'],
  ['Official mcp-clickhouse at runtime', 'Analytical answers are SQL the agent writes and executes through the official ClickHouse MCP server, not a bypass client.'],
  ['Cloud Run', 'Agent + UI and Grafana both on Cloud Run with min-instances 0; ClickHouse and the MCP server on one e2-micro VM.'],
  ['Google Cloud Storage', 'Clips and poster frames served from a public GCS bucket.'],
  ['Apache-2.0', 'The repository is public under the Apache License 2.0.'],
  ['Tears of Steel · CC BY 3.0', 'All demo footage is Blender Foundation’s Tears of Steel, attributed below.'],
]

/** About-page screenshot strip — files live in web/public/img/. */
export const SHOTS: Array<{ src: string; title: string; caption: string }> = [
  { src: '/img/ask.jpg', title: 'Ask the dailies', caption: 'Streaming answer with the cited takes playable inline at the timestamp.' },
  { src: '/img/trace.jpg', title: 'Agent trace', caption: 'Every mcp-clickhouse call, its SQL and its real row count, live.' },
  { src: '/img/takes.jpg', title: 'Takes browser', caption: 'Gemini scores, QC flags and poster frames for the whole shoot.' },
  { src: '/img/health.jpg', title: 'Production health', caption: 'Pages against plan, print ratio, flag rate — Grafana or in-app charts.' },
  { src: '/img/dpr.jpg', title: 'Daily Progress Report', caption: 'The 1 a.m. paperwork, written by the report agent and read aloud.' },
]
