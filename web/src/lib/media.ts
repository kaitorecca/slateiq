/** clip_uri / thumb_uri may be absolute (https, gs) or repo-relative ("clips/x.mp4"). */
export function mediaUrl(uri?: string | null): string | undefined {
  if (!uri) return undefined
  const u = uri.trim()
  if (!u) return undefined
  if (/^https?:\/\//i.test(u)) return u
  if (/^gs:\/\//i.test(u)) return `https://storage.googleapis.com/${u.slice(5)}`
  if (u.startsWith('/')) return u
  return `/${u.replace(/^\.\//, '')}`
}

/** Best-effort thumbnail: explicit thumb, else the clip path with a .jpg extension. */
export function thumbUrl(thumb?: string | null, clip?: string | null): string | undefined {
  const t = mediaUrl(thumb)
  if (t) return t
  const c = mediaUrl(clip)
  return c ? c.replace(/\.(mp4|mov|webm|mkv)(\?.*)?$/i, '.jpg') : undefined
}

export function fmtTime(s?: number | null): string {
  if (s == null || !Number.isFinite(s)) return '--:--'
  const total = Math.max(0, Math.round(s))
  const m = Math.floor(total / 60)
  const sec = total % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

export function takeLabel(t: { scene_number: number; shot: string; take_number: number }): string {
  return `${t.scene_number}${t.shot ?? ''}-${t.take_number}`
}
