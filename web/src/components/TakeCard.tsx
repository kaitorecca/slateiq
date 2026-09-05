import { useEffect, useState } from 'react'
import type { Take, TakeRef } from '../lib/types'
import { fmtTime, isPlayable, takeLabel, thumbUrl } from '../lib/media'
import { FlagChips, QualityBar, StatusBadge } from './StatusBadge'
import { ClipPlayer } from './ClipPlayer'

function Unpublished({ className = '' }: { className?: string }) {
  return (
    <div
      className={`relative flex aspect-video w-full flex-col items-center justify-center gap-1 overflow-hidden rounded-lg border border-dashed border-line bg-[repeating-linear-gradient(115deg,#14171B_0_10px,#0E1013_10px_20px)] px-3 text-center ${className}`}
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4 text-faint" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m4 19 6.5-7 4 4.5L17 13l3 3.5" />
        <path d="M3 3l18 18" />
      </svg>
      <span className="text-[10.5px] font-medium text-dim">Media not published</span>
    </div>
  )
}

function Thumb({ take, onPlay }: { take: TakeRef; onPlay: () => void }) {
  const [broken, setBroken] = useState(false)
  const src = thumbUrl(take.thumb_uri, take.clip_uri)
  // While an answer streams, a cited take is first known only by id + clip_uri,
  // so the poster guess 404s. The `final` event then supplies the real
  // thumb_uri -- give the new URL a fresh chance instead of staying broken.
  useEffect(() => setBroken(false), [src])
  return (
    <button
      type="button"
      onClick={onPlay}
      aria-label={`Play take ${takeLabel(take)}${take.t ? ` from ${fmtTime(take.t)}` : ''}`}
      className="group/th relative block aspect-video w-full overflow-hidden rounded-lg border border-line bg-cell"
    >
      {src && !broken ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setBroken(true)}
          className="h-full w-full object-cover opacity-85 transition duration-300 group-hover/th:scale-[1.03] group-hover/th:opacity-100"
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-[repeating-linear-gradient(115deg,#14171B_0_10px,#0E1013_10px_20px)]" />
      )}
      <span className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
      <span className="pointer-events-none absolute left-1/2 top-1/2 flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/25 bg-black/55 backdrop-blur-sm transition group-hover/th:border-slate/70 group-hover/th:bg-slate/20">
        <svg viewBox="0 0 24 24" className="ml-[2px] h-4 w-4 fill-white" aria-hidden="true">
          <path d="M8 5.2 19 12 8 18.8V5.2Z" />
        </svg>
      </span>
      {take.t != null && (
        <span className="pointer-events-none absolute bottom-1.5 right-1.5 rounded bg-black/75 px-1.5 py-[2px] font-mono text-[10px] text-slate">
          @{fmtTime(take.t)}
        </span>
      )}
    </button>
  )
}

export function TakeCard({
  take,
  onOpen,
  compact = false,
}: {
  take: Take | TakeRef
  onOpen?: (take: Take | TakeRef) => void
  compact?: boolean
}) {
  const [playing, setPlaying] = useState(false)
  const full = take as Take
  // gs:// clips in a bucket that was never published can't play anywhere --
  // show an honest placeholder instead of a play button that leads to a
  // dead <video>.
  const published = isPlayable(take.clip_uri)

  return (
    <article className="card group flex flex-col gap-2.5 p-2.5 transition hover:border-slate/35">
      {!published ? (
        <Unpublished />
      ) : playing ? (
        <ClipPlayer clipUri={take.clip_uri} thumbUri={take.thumb_uri} t={take.t} autoPlay className="aspect-video" />
      ) : (
        <Thumb take={take} onPlay={() => setPlaying(true)} />
      )}

      <div className="flex items-start justify-between gap-2 px-0.5">
        <div className="min-w-0">
          <div className="flex items-baseline gap-1.5">
            <span className="label">Sc</span>
            <span className="font-mono text-[15px] font-semibold leading-none text-ink">{takeLabel(take)}</span>
          </div>
          <p className="mt-1 truncate font-mono text-[10px] text-faint" title={take.take_id}>
            {take.take_id}
          </p>
        </div>
        <StatusBadge status={take.status} />
      </div>

      {!compact && (
        <>
          {full.summary && (
            <p className="line-clamp-3 px-0.5 text-[12px] leading-relaxed text-dim">{full.summary}</p>
          )}
          <div className="mt-auto space-y-2 px-0.5 pb-0.5">
            <FlagChips flags={full.flags} />
            <QualityBar score={full.quality_score} />
            <div className="flex items-center justify-between text-[10px] text-faint">
              <span className="font-mono">{fmtTime(full.duration_s)}</span>
              {onOpen && (
                <button
                  type="button"
                  onClick={() => onOpen(take)}
                  className="font-medium text-dim underline-offset-2 transition hover:text-slate hover:underline"
                >
                  Open take →
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </article>
  )
}
