/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GRAFANA_URL?: string
  readonly VITE_GRAFANA_DASHBOARD?: string
  readonly VITE_GRAFANA_PANELS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
