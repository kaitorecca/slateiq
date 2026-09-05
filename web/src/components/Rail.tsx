import type { ReactElement } from 'react'
import { SlateMark } from './Brand'

export interface NavItem {
  id: string
  label: string
  hint: string
  icon: ReactElement
}

const icon = (d: string) => (
  <svg viewBox="0 0 20 20" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d={d} />
  </svg>
)

export const NAV: NavItem[] = [
  { id: 'ask', label: 'Ask the Dailies', hint: 'Chat with the production brain', icon: icon('M3.5 4.5h13v9h-7.5L5 17v-3.5H3.5v-9Z') },
  { id: 'takes', label: 'Takes', hint: 'Browse every take', icon: icon('M2.5 5.5h15v9h-15v-9ZM8 8.2l4.2 2.3L8 12.8V8.2Z') },
  { id: 'health', label: 'Production Health', hint: 'Dashboards & daily report', icon: icon('M3 16.5V9M8 16.5V4.5M13 16.5v-5M18 16.5V7') },
  { id: 'about', label: 'About', hint: 'How SlateIQ works', icon: icon('M10 2.5a7.5 7.5 0 1 1 0 15 7.5 7.5 0 0 1 0-15ZM10 9v5M10 6.4h.01') },
]

export function Rail({ route, onNav }: { route: string; onNav: (id: string) => void }) {
  return (
    <nav
      aria-label="Primary"
      className="flex shrink-0 flex-row gap-1 overflow-x-auto border-b border-line bg-cell/80 px-2 py-2 backdrop-blur md:w-[230px] md:flex-col md:overflow-visible md:border-b-0 md:border-r md:px-3 md:py-4"
    >
      <div className="mb-1 hidden items-center gap-2.5 px-2 pb-3 md:flex">
        <SlateMark />
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-tight text-ink">SlateIQ</div>
          <div className="text-[10px] uppercase tracking-[.18em] text-faint">Dailies intelligence</div>
        </div>
      </div>

      {NAV.map((n) => {
        const active = route === n.id
        return (
          <button
            key={n.id}
            type="button"
            onClick={() => onNav(n.id)}
            aria-current={active ? 'page' : undefined}
            className={`group relative flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-left text-[13px] transition md:w-full ${
              active ? 'bg-raise text-ink' : 'text-dim hover:bg-raise/60 hover:text-ink'
            }`}
          >
            <span
              aria-hidden="true"
              className={`absolute left-0 top-1/2 hidden h-5 w-[2.5px] -translate-y-1/2 rounded-r bg-slate transition-opacity md:block ${
                active ? 'opacity-100' : 'opacity-0'
              }`}
            />
            <span className={active ? 'text-slate' : 'text-faint group-hover:text-dim'}>{n.icon}</span>
            <span className="min-w-0">
              <span className="block whitespace-nowrap font-medium">{n.label}</span>
              <span className="hidden truncate text-[10.5px] text-faint md:block">{n.hint}</span>
            </span>
          </button>
        )
      })}

      <div className="mt-auto hidden px-2 pt-4 md:block">
        <div className="clapper h-[6px] w-full opacity-45" />
        <p className="mt-3 text-[10px] leading-relaxed text-faint">
          Gemini · Google ADK · <span className="text-dim">ClickHouse MCP</span>
        </p>
      </div>
    </nav>
  )
}
