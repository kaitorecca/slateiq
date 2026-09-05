import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { loadRuntimeConfig } from './config'
import './index.css'

// `/api/config` hands the static build the server's env (app URL, Grafana
// dashboard + panels, MCP health). Awaited so the first render already has the
// real values; it never rejects and gives up after 3 s on the build-time
// defaults, so a slow or missing endpoint cannot stop the app booting.
const el = document.getElementById('root')
if (el) {
  void loadRuntimeConfig().finally(() => {
    createRoot(el).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  })
}
