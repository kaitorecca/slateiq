import { useEffect, useRef, useState } from 'react'
import { isPlayable, mediaUrl, thumbUrl } from '../lib/media'

interface Props {
  clipUri?: string
  thumbUri?: string
  /** seek here on load and whenever it changes */
  t?: number
  autoPlay?: boolean
  className?: string
  onTimeUpdate?: (t: number) => void
  playerRef?: (el: HTMLVideoElement | null) => void
}

export function ClipPlayer({ clipUri, thumbUri, t, autoPlay, className = '', onTimeUpdate, playerRef }: Props) {
  const ref = useRef<HTMLVideoElement | null>(null)
  const [failed, setFailed] = useState(false)
  const src = mediaUrl(clipUri)
  const poster = thumbUrl(thumbUri, clipUri)

  useEffect(() => {
    const v = ref.current
    if (!v || t == null || !Number.isFinite(t)) return
    const seek = () => {
      try {
        v.currentTime = Math.max(0, t)
      } catch {
        /* seeking before metadata — retry on loadedmetadata */
      }
    }
    if (v.readyState >= 1) seek()
    else v.addEventListener('loadedmetadata', seek, { once: true })
  }, [t, src])

  if (!src || failed) {
    // A gs:// URI in a bucket that was never made public is a publishing gap,
    // not a broken file -- say so rather than showing a dead player.
    const unpublished = !!clipUri && !isPlayable(clipUri)
    return (
      <div
        className={`flex flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-line bg-cell px-3 text-center ${className}`}
      >
        <span className="text-[11px] font-medium text-dim">
          {unpublished ? 'Media not published' : 'Clip unavailable'}
        </span>
        <span className="text-[10px] leading-snug text-faint">
          {unpublished
            ? 'This synthetic take has no footage in the public bucket.'
            : 'The clip could not be loaded.'}
        </span>
      </div>
    )
  }

  return (
    <video
      ref={(el) => {
        ref.current = el
        playerRef?.(el)
      }}
      src={src}
      poster={poster}
      controls
      playsInline
      preload="metadata"
      autoPlay={autoPlay}
      onError={() => setFailed(true)}
      onTimeUpdate={onTimeUpdate ? (e) => onTimeUpdate(e.currentTarget.currentTime) : undefined}
      className={`w-full rounded-lg border border-line bg-black ${className}`}
    />
  )
}
