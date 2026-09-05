import { useEffect, useRef } from 'react'
import type { TraceItem } from '../lib/types'
import { SqlBlock } from './SqlBlock'
import { Empty } from './States'

const AGENT_META: Record<string, { label: string; blurb: string; tone: string }> = {
  coordinator: { label: 'Coordinator', blurb: 'routes the question', tone: 'text-slate border-slate/50 bg-slate/10' },
  // ADK reports the coordinator by its registered agent name.
  slateiq_coordinator: {
    label: 'Coordinator',
    blurb: 'routes the question',
    tone: 'text-slate border-slate/50 bg-slate/10',
  },
  editor_agent: { label: 'Editor', blurb: 'take search & circled takes', tone: 'text-circled border-circled/50 bg-circled/10' },
  production_agent: { label: 'Production', blurb: 'schedule, pages, risk', tone: 'text-hold border-hold/50 bg-hold/10' },
  continuity_agent: { label: 'Continuity', blurb: 'cross-take conflicts', tone: 'text-[#D9A0F0] border-[#D9A0F0]/50 bg-[#D9A0F0]/10' },
  report_agent: { label: 'Report', blurb: 'DPR & editor log', tone: 'text-[#F09A6A] border-[#F09A6A]/50 bg-[#F09A6A]/10' },
}

/** Tools that really are served by the official mcp-clickhouse server. */
const MCP_TOOLS = new Set(['run_query', 'list_tables', 'list_databases', 'describe_table'])

function agentMeta(name: string) {
  return (
    AGENT_META[name] ?? {
      label: name.replace(/_/g, ' '),
      blurb: 'sub-agent',
      tone: 'text-dim border-line bg-raise',
    }
  )
}

function ToolIcon({ name }: { name: string }) {
  const q = name === 'run_query'
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      {q ? (
        <>
          <ellipse cx="8" cy="4" rx="5.2" ry="2.2" />
          <path d="M2.8 4v8c0 1.2 2.3 2.2 5.2 2.2s5.2-1 5.2-2.2V4" />
          <path d="M2.8 8c0 1.2 2.3 2.2 5.2 2.2s5.2-1 5.2-2.2" />
        </>
      ) : (
        <>
          <path d="M6.5 2.5 3 6l3.5 3.5" />
          <path d="M9.5 6.5 13 10l-3.5 3.5" />
        </>
      )}
    </svg>
  )
}

export function TraceRow({ item }: { item: TraceItem }) {
  if (item.kind === 'agent') {
    const m = agentMeta(item.name)
    return (
      <li className="animate-rise">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2 w-2 shrink-0 items-center justify-center">
            <span className={`absolute h-2 w-2 rounded-full ${m.tone.split(' ')[0].replace('text-', 'bg-')}`} />
          </span>
          <span className={`rounded-md border px-2 py-[3px] text-[11px] font-semibold capitalize ${m.tone}`}>
            {m.label} agent
          </span>
          <span className="truncate text-[11px] text-faint">{m.blurb}</span>
        </div>
      </li>
    )
  }

  if (item.kind === 'error') {
    return (
      <li className="animate-rise rounded-lg border border-ng/40 bg-ng/10 px-3 py-2 text-[12px] text-ng">
        {item.summary ?? item.name}
      </li>
    )
  }

  const isResult = item.kind === 'tool_result'
  // `transfer_to_agent` is ADK's own routing call, not a ClickHouse MCP tool --
  // labelling it "MCP call" would overstate the partner evidence.
  const isMcp = MCP_TOOLS.has(item.name)
  const rows = item.rows != null && item.rows >= 0 ? item.rows : null
  // ADK's transfer_to_agent returns a bare `null` -- don't print it.
  const summary = item.summary && item.summary.trim() !== 'null' ? item.summary : undefined
  return (
    <li className="animate-rise rounded-xl border border-line bg-panel/60">
      <div className="flex items-center gap-2 border-b border-line/70 px-3 py-2">
        <span className={isResult ? 'text-circled' : 'text-slate'}>
          <ToolIcon name={item.name} />
        </span>
        <span className="font-mono text-[11px] font-semibold text-ink">{item.name}</span>
        {isMcp ? (
          <span
            className="chip border-slate/40 bg-slate/10 px-1.5 py-[1px] font-mono text-[9.5px] leading-none text-slate"
            title="Executed by the official mcp-clickhouse server at runtime"
          >
            via mcp-clickhouse
          </span>
        ) : (
          <span
            className="chip px-1.5 py-[1px] text-[9.5px] leading-none text-faint"
            title="ADK's own sub-agent routing — not a ClickHouse call"
          >
            hand-off
          </span>
        )}
        {isResult && <span className="label">result</span>}
        <span className="ml-auto flex items-center gap-2">
          {rows != null && (
            <span className="chip border-circled/30 bg-circled/10 px-2 py-[2px] font-mono text-[10px] text-circled">
              {rows.toLocaleString()} {rows === 1 ? 'row' : 'rows'}
            </span>
          )}
          {item.pending && (
            <span className="chip animate-blip border-slate/30 bg-slate/10 px-2 py-[2px] text-[10px] text-slate">
              running
            </span>
          )}
        </span>
      </div>
      <div className="space-y-2 p-2">
        {item.query ? (
          <SqlBlock sql={item.query} dense />
        ) : item.args && Object.keys(item.args).length > 0 ? (
          <pre className="overflow-x-auto rounded-lg border border-line bg-cell p-2.5 font-mono text-[11px] text-dim">
            {JSON.stringify(item.args, null, 2)}
          </pre>
        ) : null}
        {summary && <p className="px-1 pb-0.5 text-[11.5px] leading-relaxed text-dim">{summary}</p>}
      </div>
    </li>
  )
}

export function AgentTrace({ items, live }: { items: TraceItem[]; live?: boolean }) {
  const endRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [items.length])

  const queries = items.filter((i) => i.kind === 'tool_call' && i.query).length
  const rows = items.reduce((n, i) => n + (i.rows != null && i.rows > 0 ? i.rows : 0), 0)

  return (
    <section className="flex h-full min-h-0 flex-col" aria-label="Agent trace">
      <header className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className={`h-1.5 w-1.5 rounded-full ${live ? 'animate-blip bg-slate' : 'bg-faint'}`} />
        <h2 className="text-[12px] font-semibold uppercase tracking-[.14em] text-ink">Agent trace</h2>
        <span className="ml-auto flex items-center gap-1.5">
          <span className="chip px-2 py-[2px] font-mono text-[10px]">{queries} SQL</span>
          <span className="chip px-2 py-[2px] font-mono text-[10px]">{rows.toLocaleString()} rows</span>
        </span>
      </header>
      <p className="border-b border-line/60 px-4 py-2 text-[11px] leading-relaxed text-faint">
        Every statement below was generated by the ADK agent and executed against ClickHouse through the official{' '}
        <span className="font-mono text-dim">mcp-clickhouse</span> server at runtime.
      </p>
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {items.length === 0 ? (
          <Empty title="No tool calls yet" hint="Ask a question and the agent's MCP calls, SQL and row counts stream in here live." />
        ) : (
          <ol className="space-y-2.5">
            {items.map((i) => (
              <TraceRow key={i.id} item={i} />
            ))}
          </ol>
        )}
        <div ref={endRef} />
      </div>
    </section>
  )
}
