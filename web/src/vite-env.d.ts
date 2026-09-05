/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GRAFANA_URL?: string
  readonly VITE_GRAFANA_DASHBOARD?: string
  readonly VITE_GRAFANA_PANELS?: string
  /** Hosted SlateIQ agent + UI (Cloud Run). */
  readonly VITE_APP_URL?: string
  /** Unauthenticated health route of the official mcp-clickhouse server. */
  readonly VITE_MCP_HEALTH_URL?: string
  /** Comma-separated public-read GCS buckets whose gs:// URIs actually resolve. */
  readonly VITE_PUBLIC_MEDIA_BUCKETS?: string
  /** Comma-separated scene numbers that have real footage ingested. */
  readonly VITE_FOOTAGE_SCENES?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
