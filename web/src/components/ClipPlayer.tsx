import { useEffect, useRef, useState } from 'react'
import { mediaUrl, thumbUrl } from '../lib/media'

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
    return (
      <div
        className={`flex items-center justify-center rounded-lg border border-dashed border-line bg-cell text-[11px] text-faint ${className}`}
      >
        clip unavailable
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
