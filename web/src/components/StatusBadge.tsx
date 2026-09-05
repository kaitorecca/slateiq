import type { TakeStatus } from '../lib/types'

const MAP: Record<string, { label: string; cls: string }> = {
  circled: { label: 'Circled', cls: 'border-circled/50 bg-circled/12 text-circled' },
  ng: { label: 'NG', cls: 'border-ng/50 bg-ng/12 text-ng' },
  hold: { label: 'Hold', cls: 'border-hold/50 bg-hold/12 text-hold' },
}

export function StatusBadge({ status, className = '' }: { status: TakeStatus; className?: string }) {
  const key = String(status ?? '').toLowerCase()
  const s = MAP[key] ?? { label: status || 'unknown', cls: 'border-line bg-raise text-dim' }
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-[3px] text-[10px] font-semibold uppercase tracking-wider ${s.cls} ${className}`}
    >
      {key === 'circled' && (
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" aria-hidden="true">
          <circle cx="6" cy="6" r="4.4" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      )}
      {s.label}
    </span>
  )
}

export function QualityBar({ score }: { score?: number | null }) {
  if (score == null || !Number.isFinite(score)) return null
  const pct = Math.max(0, Math.min(100, score <= 1 ? score * 100 : score))
  const tone = pct >= 75 ? 'bg-circled' : pct >= 50 ? 'bg-slate' : 'bg-ng'
  return (
    <div className="flex items-center gap-2" title={`Quality ${Math.round(pct)}/100`}>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-raise">
        <div className={`h-full rounded-full ${tone} transition-[width] duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[10px] tabular-nums text-faint">{Math.round(pct)}</span>
    </div>
  )
}

export function FlagChips({ flags, max = 4 }: { flags?: string[]; max?: number }) {
  if (!flags?.length) return null
  const shown = flags.slice(0, max)
  return (
    <div className="flex flex-wrap gap-1">
      {shown.map((f) => (
        <span key={f} className="chip border-ng/25 bg-ng/10 px-2 py-[2px] text-[10px] text-ng/90">
          {f.replace(/_/g, ' ')}
        </span>
      ))}
      {flags.length > max && <span className="chip px-2 py-[2px] text-[10px]">+{flags.length - max}</span>}
    </div>
  )
}
