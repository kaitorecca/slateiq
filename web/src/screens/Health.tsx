import { useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getDpr, getTakes, tts } from '../lib/api'
import type { Take } from '../lib/types'
import { useAsync } from '../lib/hooks'
import { Markdown } from '../components/Markdown'
import { Empty, ErrorBox, Skeleton, Spinner } from '../components/States'

const GRAFANA_URL = (import.meta.env.VITE_GRAFANA_URL as string | undefined)?.replace(/\/$/, '')
const GRAFANA_DASH = (import.meta.env.VITE_GRAFANA_DASHBOARD as string | undefined) ?? 'slateiq/production-health'
const GRAFANA_PANELS = ((import.meta.env.VITE_GRAFANA_PANELS as string | undefined) ?? '1:Shooting ratio by scene,2:Pages vs plan,3:Flag rate,4:Camera hours')
  .split(',')
  .map((p) => p.trim())
  .filter(Boolean)
  .map((p) => {
    const [id, ...rest] = p.split(':')
    return { id: id.trim(), title: rest.join(':').trim() || `Panel ${id}` }
  })

/** Muted, filmic chart palette that sits on the dark ground without glaring. */
const C = { circled: '#4E9E6B', hold: '#4C82BD', ng: '#B8514A', slate: '#D2A03A', dim: '#7A5F1E' }
const AXIS = { stroke: '#3A414A', fontSize: 11 }
const TOOLTIP = {
  contentStyle: {
    background: '#14171B',
    border: '1px solid #252A31',
    borderRadius: 10,
    fontSize: 12,
    color: '#E9E7E2',
  },
  labelStyle: { color: '#9AA1AB', fontSize: 11 },
  cursor: { fill: 'rgba(255,255,255,.04)' },
}

function Panel({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <section className="card p-4">
      <header className="mb-3">
        <h3 className="text-[13px] font-semibold text-ink">{title}</h3>
        {note && <p className="mt-0.5 text-[11px] text-faint">{note}</p>}
      </header>
      {children}
    </section>
  )
}

function FallbackCharts({ takes }: { takes: Take[] }) {
  const byScene = useMemo(() => {
    const m = new Map<number, { scene: string; circled: number; ng: number; hold: number; q: number; n: number }>()
    for (const t of takes) {
      const k = t.scene_number
      const row = m.get(k) ?? { scene: `Sc ${k}`, circled: 0, ng: 0, hold: 0, q: 0, n: 0 }
      const s = String(t.status).toLowerCase()
      if (s === 'circled') row.circled++
      else if (s === 'ng') row.ng++
      else row.hold++
      if (t.quality_score != null) {
        row.q += t.quality_score <= 1 ? t.quality_score * 100 : t.quality_score
        row.n++
      }
      m.set(k, row)
    }
    return [...m.entries()].sort((a, b) => a[0] - b[0]).map(([, v]) => ({ ...v, avgQuality: v.n ? Math.round(v.q / v.n) : 0 }))
  }, [takes])

  const flags = useMemo(() => {
    const m = new Map<string, number>()
    for (const t of takes) for (const f of t.flags ?? []) m.set(f, (m.get(f) ?? 0) + 1)
    return [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([flag, count]) => ({ flag: flag.replace(/_/g, ' '), count }))
  }, [takes])

  const ratio = useMemo(
    () =>
      byScene.map((s) => ({
        scene: s.scene,
        ratio: Number(((s.circled + s.ng + s.hold) / Math.max(1, s.circled)).toFixed(2)),
      })),
    [byScene],
  )

  if (!takes.length) return <Empty title="No take data yet" hint="Charts fill in once ClickHouse has takes." />

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Panel title="Takes by scene" note="Circled / NG / hold, from /api/takes">
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={byScene} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#1D2127" vertical={false} />
            <XAxis dataKey="scene" {...AXIS} tickLine={false} />
            <YAxis {...AXIS} tickLine={false} axisLine={false} allowDecimals={false} />
            <Tooltip {...TOOLTIP} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#9AA1AB' }} />
            <Bar dataKey="circled" stackId="s" fill={C.circled} radius={[0, 0, 0, 0]} />
            <Bar dataKey="hold" stackId="s" fill={C.hold} />
            <Bar dataKey="ng" stackId="s" fill={C.ng} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      <Panel title="Average quality score by scene" note="Gemini per-take score, 0–100">
        <ResponsiveContainer width="100%" height={230}>
          <LineChart data={byScene} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#1D2127" vertical={false} />
            <XAxis dataKey="scene" {...AXIS} tickLine={false} />
            <YAxis {...AXIS} domain={[0, 100]} tickLine={false} axisLine={false} />
            <Tooltip {...TOOLTIP} />
            <Line type="monotone" dataKey="avgQuality" stroke={C.slate} strokeWidth={2} dot={{ r: 2.5, fill: C.slate }} />
          </LineChart>
        </ResponsiveContainer>
      </Panel>

      <Panel title="Most common flags" note="QC issues detected across all takes">
        {flags.length ? (
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={flags} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 24 }}>
              <CartesianGrid stroke="#1D2127" horizontal={false} />
              <XAxis type="number" {...AXIS} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="flag" width={92} {...AXIS} tickLine={false} axisLine={false} />
              <Tooltip {...TOOLTIP} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {flags.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? C.ng : C.dim} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Empty title="No flags recorded" />
        )}
      </Panel>

      <Panel title="Shooting ratio by scene" note="Takes rolled per circled take — lower is tighter">
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={ratio} margin={{ top: 4, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#1D2127" vertical={false} />
            <XAxis dataKey="scene" {...AXIS} tickLine={false} />
            <YAxis {...AXIS} tickLine={false} axisLine={false} />
            <Tooltip {...TOOLTIP} />
            <Bar dataKey="ratio" fill={C.hold} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  )
}

function GrafanaPanels() {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      {GRAFANA_PANELS.map((p) => (
        <div key={p.id} className="card overflow-hidden">
          <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
            <h3 className="text-[13px] font-semibold text-ink">{p.title}</h3>
            <span className="chip ml-auto px-2 py-[2px] text-[10px]">Grafana · ClickHouse</span>
          </div>
          <iframe
            title={p.title}
            src={`${GRAFANA_URL}/d-solo/${GRAFANA_DASH}?orgId=1&panelId=${p.id}&theme=dark&kiosk`}
            className="h-[260px] w-full border-0 bg-cell"
            loading="lazy"
          />
        </div>
      ))}
    </div>
  )
}

function DprCard() {
  const [day, setDay] = useState(12)
  const [markdown, setMarkdown] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [speaking, setSpeaking] = useState(false)
  const [ttsError, setTtsError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    setTtsError(null)
    setAudioUrl(null)
    try {
      const r = await getDpr(day)
      setMarkdown(r.markdown)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const readAloud = async () => {
    if (!markdown) return
    setSpeaking(true)
    setTtsError(null)
    try {
      const plain = markdown
        .replace(/```[\s\S]*?```/g, ' ')
        .replace(/[#*_>`|-]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 4000)
      const url = await tts(plain)
      setAudioUrl(url)
      window.setTimeout(() => void audioRef.current?.play().catch(() => undefined), 60)
    } catch (e: unknown) {
      setTtsError(e instanceof Error ? e.message : String(e))
    } finally {
      setSpeaking(false)
    }
  }

  return (
    <section className="card overflow-hidden">
      <header className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
        <div>
          <h3 className="text-[13px] font-semibold text-ink">Daily Progress Report</h3>
          <p className="text-[11px] text-faint">Written by the report agent from ClickHouse, not by a human at 1 a.m.</p>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <label htmlFor="dpr-day" className="label">
            Day
          </label>
          <input
            id="dpr-day"
            type="number"
            min={1}
            max={60}
            value={day}
            onChange={(e) => setDay(Math.max(1, Number(e.target.value) || 1))}
            className="w-16 rounded-lg border border-line bg-raise px-2 py-1.5 text-[12.5px] text-ink focus:border-slate/60 focus:outline-none"
          />
          <button className="btn btn-primary" onClick={() => void generate()} disabled={loading}>
            {loading && <Spinner className="h-3.5 w-3.5" />}
            {loading ? 'Generating…' : 'Generate Daily Progress Report'}
          </button>
          <button className="btn" onClick={() => void readAloud()} disabled={!markdown || speaking}>
            {speaking ? <Spinner className="h-3.5 w-3.5" /> : <span aria-hidden="true">🔊</span>}
            Read it aloud
          </button>
        </div>
      </header>

      <div className="p-4">
        {error && <ErrorBox message={error} onRetry={() => void generate()} />}
        {ttsError && <div className="mb-3"><ErrorBox message={`Gemini TTS: ${ttsError}`} /></div>}
        {audioUrl && (
          <audio ref={audioRef} src={audioUrl} controls className="mb-4 w-full" aria-label="Spoken daily progress report" />
        )}
        {loading && !markdown ? (
          <div className="space-y-2">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-11/12" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        ) : markdown ? (
          <div className="max-h-[560px] overflow-y-auto rounded-lg border border-line bg-cell/60 p-5">
            <Markdown>{markdown}</Markdown>
          </div>
        ) : (
          !error && (
            <Empty
              title="No report generated yet"
              hint="Pick a shooting day and hit Generate — the agent queries ClickHouse through MCP and writes the DPR, then Gemini TTS can read it to you."
            />
          )
        )}
      </div>
    </section>
  )
}

export function Health() {
  const { data, error, loading, reload } = useAsync<Take[]>(() => getTakes(null), [])

  return (
    <div className="h-full overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto w-full max-w-[1400px] space-y-6">
        <header>
          <div className="clapper mb-3 h-[7px] w-16 opacity-70" />
          <h1 className="text-2xl font-semibold tracking-tight text-ink">Production health</h1>
          <p className="mt-1 text-[13px] text-dim">
            {GRAFANA_URL
              ? 'Grafana panels served straight off the ClickHouse datasource.'
              : 'In-app charts derived from the take index. Set VITE_GRAFANA_URL to embed the Grafana dashboard instead.'}
          </p>
        </header>

        {GRAFANA_URL ? (
          <GrafanaPanels />
        ) : loading ? (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[290px]" />
            ))}
          </div>
        ) : error ? (
          <ErrorBox message={error} onRetry={reload} />
        ) : (
          <FallbackCharts takes={data ?? []} />
        )}

        <DprCard />
      </div>
    </div>
  )
}
