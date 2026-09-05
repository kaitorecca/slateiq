import type { Health } from '../lib/types'

function Dot({ label, state }: { label: string; state: 'up' | 'down' | 'unknown' }) {
  const tone =
    state === 'up' ? 'bg-circled shadow-[0_0_8px_rgba(95,191,127,.7)]' : state === 'down' ? 'bg-ng' : 'bg-faint'
  return (
    <span
      className="flex items-center gap-1.5"
      title={`${label}: ${state}`}
      role="status"
      aria-label={`${label} ${state}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${tone} ${state === 'unknown' ? 'animate-blip' : ''}`} />
      <span className="text-[11px] font-medium text-dim">{label}</span>
    </span>
  )
}

export function HealthDots({ health, error }: { health: Health | null; error?: string | null }) {
  const s = (v?: string): 'up' | 'down' | 'unknown' => (v === 'up' ? 'up' : v === 'down' ? 'down' : 'unknown')
  const state = error ? { mcp: 'down' as const, clickhouse: 'down' as const } : { mcp: s(health?.mcp), clickhouse: s(health?.clickhouse) }
  return (
    <div className="flex items-center gap-3.5 rounded-full border border-line bg-panel/70 px-3 py-1.5">
      <Dot label="MCP" state={state.mcp} />
      <span className="h-3 w-px bg-line" />
      <Dot label="ClickHouse" state={state.clickhouse} />
    </div>
  )
}
