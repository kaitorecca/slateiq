/**
 * Configuration for the About page's "Live" section, the embedded Grafana
 * panels and the media-availability check in the takes gallery.
 *
 * Two layers, in order of precedence:
 *
 *  1. **Runtime** — `GET /api/config`, fetched once before the app renders
 *     (`loadRuntimeConfig()` in `main.tsx`). This is the layer that matters in
 *     production: `web/` is a *static* Vite build, so `import.meta.env.VITE_*`
 *     is frozen at build time and server env vars (`GRAFANA_URL`,
 *     `CLIPS_BASE_URL`, …) could never otherwise reach the browser.
 *  2. **Build-time `VITE_*` / the literals below** — the fallback, used in dev
 *     and if `/api/config` is unreachable. The literals are the endpoints
 *     recorded in `deploy/OUTPUT.md`.
 *
 * The exported URLs are `let` bindings on purpose: ES module live bindings mean
 * `applyRuntimeConfig()` updates every importer, including modules that already
 * captured the value.
 */

const env = import.meta.env

const clean = (v: string | undefined, fallback: string): string =>
  (v && v.trim() ? v.trim() : fallback).replace(/\/+$/, '')

/** Public source. */
export let REPO_URL = clean(env.VITE_REPO_URL, 'https://github.com/kaitorecca/slateiq')

/** The hosted SlateIQ agent + UI (Cloud Run, min-instances 0). */
export let APP_URL = clean(env.VITE_APP_URL, 'https://slateiq-957930801789.us-central1.run.app')

/** Grafana on Cloud Run — the Production Health dashboard. */
export let GRAFANA_URL = clean(env.VITE_GRAFANA_URL, 'https://slateiq-grafana-hbissixc2q-uc.a.run.app')

/**
 * The Production Health dashboard's UID and the panels embedded on the health
 * screen, as `id:title`. Both must match `deploy/grafana/dashboards/
 * slateiq-production-health.json` — a wrong UID makes every `d-solo` iframe
 * 404, and a wrong title mislabels a real chart, which is worse.
 */
export let GRAFANA_DASH_UID = clean(env.VITE_GRAFANA_DASHBOARD, 'slateiq-prod-health')

export type GrafanaPanel = { id: string; title: string }

const parsePanels = (spec: string): GrafanaPanel[] =>
  spec
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => {
      const [id, ...rest] = p.split(':')
      return { id: id.trim(), title: rest.join(':').trim() || `Panel ${id.trim()}` }
    })
    .filter((p) => p.id)

export let GRAFANA_PANELS: GrafanaPanel[] = parsePanels(
  env.VITE_GRAFANA_PANELS ??
    '2:Schedule position,1:Pages planned vs shot per day,3:Print ratio (takes per circled take) by scene,8:Scenes at risk',
)

/** Unauthenticated health route of the official mcp-clickhouse server on the VM. */
export let MCP_HEALTH_URL = clean(env.VITE_MCP_HEALTH_URL, 'https://35.239.36.85.sslip.io/health')

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


// ---------------------------------------------------------------------------
// Runtime config (GET /api/config)
// ---------------------------------------------------------------------------
type RuntimeConfig = {
  app_url?: string
  grafana_url?: string
  grafana_dash_uid?: string
  grafana_panels?: Array<{ id?: string | number; title?: string }>
  mcp_health_url?: string
  repo_url?: string
}

function applyRuntimeConfig(cfg: RuntimeConfig): void {
  APP_URL = clean(cfg.app_url, APP_URL)
  GRAFANA_URL = clean(cfg.grafana_url, GRAFANA_URL)
  GRAFANA_DASH_UID = clean(cfg.grafana_dash_uid, GRAFANA_DASH_UID)
  MCP_HEALTH_URL = clean(cfg.mcp_health_url, MCP_HEALTH_URL)
  REPO_URL = clean(cfg.repo_url, REPO_URL)
  const panels = (cfg.grafana_panels ?? [])
    .map((p) => ({ id: String(p?.id ?? '').trim(), title: String(p?.title ?? '').trim() }))
    .filter((p) => p.id)
    .map((p) => ({ id: p.id, title: p.title || `Panel ${p.id}` }))
  if (panels.length) GRAFANA_PANELS = panels
}

/**
 * Fetch `/api/config` once at boot. Never rejects and never blocks the app for
 * long: on any failure or after 3 s the build-time defaults above stand.
 */
export async function loadRuntimeConfig(): Promise<void> {
  try {
    const ctrl = new AbortController()
    const timer = window.setTimeout(() => ctrl.abort(), 3000)
    const res = await fetch('/api/config', { signal: ctrl.signal })
    window.clearTimeout(timer)
    if (res.ok) applyRuntimeConfig((await res.json()) as RuntimeConfig)
  } catch {
    /* keep the build-time defaults */
  }
}
