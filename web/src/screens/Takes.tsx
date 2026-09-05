import { useEffect, useMemo, useState } from 'react'
import { getTakeEvents, getTakes } from '../lib/api'
import type { Take, TakeEvent } from '../lib/types'
import { useAsync } from '../lib/hooks'
import { TakeCard } from '../components/TakeCard'
import { ClipPlayer } from '../components/ClipPlayer'
import { Drawer } from '../components/Drawer'
import { Empty, ErrorBox, Skeleton } from '../components/States'
import { FlagChips, QualityBar, StatusBadge } from '../components/StatusBadge'
import { fmtTime } from '../lib/media'

const STATUSES = [
  { id: 'all', label: 'All' },
  { id: 'circled', label: 'Circled' },
  { id: 'ng', label: 'NG' },
  { id: 'hold', label: 'Hold' },
] as const
type StatusFilter = (typeof STATUSES)[number]['id']

function EventTimeline({
  events,
  duration,
  onSeek,
  current,
}: {
  events: TakeEvent[]
  duration: number
  onSeek: (t: number) => void
  current: number
}) {
  const d = duration > 0 ? duration : Math.max(1, ...events.map((e) => e.t || 0))
  return (
    <div className="space-y-3">
      <div className="relative h-9 rounded-lg border border-line bg-cell">
        <div
          className="absolute bottom-0 top-0 w-px bg-slate/80"
          style={{ left: `${Math.min(100, (current / d) * 100)}%` }}
          aria-hidden="true"
        />
        {events.map((e, i) => {
          const left = `${Math.min(99.5, Math.max(0, (e.t / d) * 100))}%`
          const tone = e.kind === 'flag' ? 'bg-ng' : e.kind === 'dialogue' ? 'bg-hold' : 'bg-faint'
          return (
            <button
              key={i}
              type="button"
              onClick={() => onSeek(e.t)}
              title={`${fmtTime(e.t)} · ${e.flag ?? e.speaker ?? e.kind}`}
              aria-label={`Seek to ${fmtTime(e.t)} — ${e.flag ?? e.speaker ?? e.kind}`}
              className={`absolute top-1.5 h-6 w-[3px] rounded-full ${tone} opacity-70 transition hover:h-7 hover:opacity-100`}
              style={{ left }}
            />
          )
        })}
      </div>
      <ol className="max-h-72 space-y-1 overflow-y-auto pr-1">
        {events.map((e, i) => (
          <li key={i}>
            <button
              type="button"
              onClick={() => onSeek(e.t)}
              className="flex w-full items-start gap-2.5 rounded-lg px-2 py-1.5 text-left transition hover:bg-raise/70"
            >
              <span className="mt-[1px] font-mono text-[11px] tabular-nums text-slate">{fmtTime(e.t)}</span>
              {e.kind === 'flag' ? (
                <span className="chip border-ng/30 bg-ng/10 px-2 py-[1px] text-[10px] text-ng">
                  {(e.flag ?? 'flag').replace(/_/g, ' ')}
                </span>
              ) : (
                <span className="min-w-0 flex-1 text-[12px] leading-relaxed text-dim">
                  {e.speaker && <b className="mr-1.5 font-semibold uppercase tracking-wide text-ink">{e.speaker}</b>}
                  {e.text ?? e.kind}
                </span>
              )}
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}

function TakeDrawer({ take, onClose }: { take: Take | null; onClose: () => void }) {
  const [events, setEvents] = useState<TakeEvent[] | null>(null)
  const [loadingEvents, setLoadingEvents] = useState(false)
  const [video, setVideo] = useState<HTMLVideoElement | null>(null)
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    setEvents(null)
    setCurrent(0)
    if (!take) return
    let alive = true
    setLoadingEvents(true)
    getTakeEvents(take.take_id)
      .then((e) => alive && setEvents(e))
      .finally(() => alive && setLoadingEvents(false))
    return () => {
      alive = false
    }
  }, [take])

  const seek = (t: number) => {
    if (!video) return
    video.currentTime = Math.max(0, t)
    void video.play().catch(() => undefined)
  }

  return (
    <Drawer
      open={!!take}
      onClose={onClose}
      title={
        take ? `Scene ${take.scene_number} · Shot ${take.shot ?? '--'} · Take ${take.take_number}` : ''
      }
      subtitle={take?.take_id}
    >
      {take && (
        <div className="space-y-5">
          <ClipPlayer
            clipUri={take.clip_uri}
            thumbUri={take.thumb_uri}
            playerRef={setVideo}
            onTimeUpdate={setCurrent}
            className="aspect-video"
          />

          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={take.status} />
            <span className="chip font-mono text-[10px]">{fmtTime(take.duration_s)}</span>
            <FlagChips flags={take.flags} max={8} />
          </div>

          {take.quality_score != null && (
            <div>
              <div className="label mb-1.5">Quality score</div>
              <QualityBar score={take.quality_score} />
            </div>
          )}

          {take.summary && (
            <div>
              <div className="label mb-1.5">Gemini summary</div>
              <p className="rounded-lg border border-line bg-panel/60 p-3 text-[12.5px] leading-relaxed text-dim">
                {take.summary}
              </p>
            </div>
          )}

          <div>
            <div className="label mb-2">Transcript & flag timeline</div>
            {loadingEvents ? (
              <Skeleton className="h-24 w-full" />
            ) : events?.length ? (
              <EventTimeline events={events} duration={take.duration_s ?? 0} onSeek={seek} current={current} />
            ) : (
              <Empty
                title="No event detail for this take"
                hint="Timestamped dialogue and flags appear here when the ingest pipeline has written take_event rows."
              />
            )}
          </div>
        </div>
      )}
    </Drawer>
  )
}

export function Takes() {
  const [scene, setScene] = useState<string | null>(null)
  const [status, setStatus] = useState<StatusFilter>('all')
  const [selected, setSelected] = useState<Take | null>(null)
  const { data, error, loading, reload } = useAsync<Take[]>(() => getTakes(scene), [scene])

  const scenes = useMemo(() => {
    const s = new Set<string>()
    for (const t of data ?? []) if (t.scene_number != null && t.scene_number !== '') s.add(String(t.scene_number))
    return [...s].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
  }, [data])

  const [allScenes, setAllScenes] = useState<string[]>([])
  useEffect(() => {
    if (scene == null && scenes.length) setAllScenes(scenes)
  }, [scene, scenes])

  const shown = useMemo(
    () => (data ?? []).filter((t) => status === 'all' || String(t.status).toLowerCase() === status),
    [data, status],
  )

  const counts = useMemo(() => {
    const c = { circled: 0, ng: 0, hold: 0 }
    for (const t of data ?? []) {
      const k = String(t.status).toLowerCase() as keyof typeof c
      if (k in c) c[k] += 1
    }
    return c
  }, [data])

  return (
    <div className="h-full overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto w-full max-w-[1400px] space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="clapper mb-3 h-[7px] w-16 opacity-70" />
            <h1 className="text-2xl font-semibold tracking-tight text-ink">Takes</h1>
            <p className="mt-1 text-[13px] text-dim">
              Everything the camera rolled, scored and flagged by Gemini during ingest.
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-faint">
            <span className="chip border-circled/30 bg-circled/10 text-circled">{counts.circled} circled</span>
            <span className="chip border-ng/30 bg-ng/10 text-ng">{counts.ng} NG</span>
            <span className="chip border-hold/30 bg-hold/10 text-hold">{counts.hold} hold</span>
          </div>
        </header>

        <div className="flex flex-wrap items-center gap-4 rounded-xl border border-line bg-panel/50 px-3 py-2.5">
          <div className="flex items-center gap-2">
            <label htmlFor="scene" className="label">
              Scene
            </label>
            <select
              id="scene"
              value={scene ?? ''}
              onChange={(e) => setScene(e.target.value === '' ? null : e.target.value)}
              className="rounded-lg border border-line bg-raise px-2.5 py-1.5 text-[12.5px] text-ink focus:border-slate/60 focus:outline-none"
            >
              <option value="">All scenes</option>
              {(allScenes.length ? allScenes : scenes).map((s) => (
                <option key={s} value={s}>
                  Scene {s}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1.5" role="group" aria-label="Filter by status">
            {STATUSES.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setStatus(s.id)}
                aria-pressed={status === s.id}
                className={`chip px-2.5 py-1 transition ${
                  status === s.id ? 'border-slate/60 bg-slate/15 text-slate' : 'hover:text-ink'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <span className="ml-auto font-mono text-[11px] text-faint">
            {loading ? 'loading…' : `${shown.length} take${shown.length === 1 ? '' : 's'}`}
          </span>
        </div>

        {error && <ErrorBox message={error} onRetry={reload} />}

        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-[300px]" />
            ))}
          </div>
        ) : shown.length === 0 && !error ? (
          <Empty
            title="No takes match these filters"
            hint="Try another scene or clear the status filter. If the list is empty everywhere, the ingest pipeline has not written to ClickHouse yet."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {shown.map((t) => (
              <TakeCard key={t.take_id} take={t} onOpen={(x) => setSelected(x as Take)} />
            ))}
          </div>
        )}
      </div>

      <TakeDrawer take={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
