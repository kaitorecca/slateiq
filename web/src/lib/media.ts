import { PUBLIC_MEDIA_BUCKETS } from '../config'

/** `gs://bucket/key` -> bucket, else null. */
function gsBucket(uri: string): string | null {
  const m = /^gs:\/\/([^/]+)\//i.exec(uri.trim())
  return m ? m[1] : null
}

/**
 * True when the URI points at media a browser can actually load: a relative
 * path served by this app, an https URL, or a `gs://` object in a bucket we
 * know is public-read. The synthetic takes point at `gs://slateiq-dailies/…`,
 * a bucket that was never published — those render a "media not published"
 * card rather than a broken <video>.
 */
export function isPlayable(uri?: string | null): boolean {
  const u = uri?.trim()
  if (!u) return false
  const bucket = gsBucket(u)
  if (bucket) return PUBLIC_MEDIA_BUCKETS.includes(bucket)
  return true
}

/** clip_uri / thumb_uri may be absolute (https, gs) or repo-relative ("clips/x.mp4"). */
export function mediaUrl(uri?: string | null): string | undefined {
  if (!uri) return undefined
  const u = uri.trim()
  if (!u) return undefined
  if (/^https?:\/\//i.test(u)) return u
  if (/^gs:\/\//i.test(u)) {
    // Only rewrite objects we know are publicly readable.
    return isPlayable(u) ? `https://storage.googleapis.com/${u.slice(5)}` : undefined
  }
  if (u.startsWith('/')) return u
  return `/${u.replace(/^\.\//, '')}`
}

/**
 * Best-effort thumbnail: the explicit `thumb_uri` when we have one, else the
 * poster frame derived from the clip path. Posters live under `thumbs/`
 * alongside `clips/` both on disk and in the GCS bucket, so map the directory
 * as well as the extension -- guessing `clips/<id>.jpg` only ever 404s, and a
 * cited take is known by `clip_uri` alone until the `final` event lands.
 */
export function thumbUrl(thumb?: string | null, clip?: string | null): string | undefined {
  const t = mediaUrl(thumb)
  if (t) return t
  const c = mediaUrl(clip)
  if (!c) return undefined
  return c.replace(/\/clips\//i, '/thumbs/').replace(/\.(mp4|mov|webm|mkv)(\?.*)?$/i, '.jpg')
}

export function fmtTime(s?: number | null): string {
  if (s == null || !Number.isFinite(s)) return '--:--'
  const total = Math.max(0, Math.round(s))
  const m = Math.floor(total / 60)
  const sec = total % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

/** `TOS-D12-S14A-A-02-B` -> scene 14A, shot A, take 2, camera B. */
export function parseTakeId(takeId?: string | null) {
  const m = /-S([0-9]+[A-Z]?)-([A-Z]+)-([0-9]+)(?:-([A-Z]))?$/i.exec(takeId ?? '')
  if (!m) return null
  return { scene_number: m[1], shot: m[2], take_number: Number(m[3]), camera: m[4] }
}

/**
 * Slate label, e.g. `14A/A/2`. Agents cite takes by `take_id` only, so fall
 * back to parsing the id rather than rendering "undefined-undefined".
 */
export function takeLabel(t: {
  scene_number?: string | number | null
  shot?: string | null
  take_number?: number | null
  take_id?: string | null
}): string {
  const p = parseTakeId(t.take_id)
  const scene = t.scene_number ?? p?.scene_number
  const shot = t.shot ?? p?.shot
  const take = t.take_number ?? p?.take_number
  if (scene == null && shot == null && take == null) return t.take_id ?? '--'
  return [scene, shot, take].filter((v) => v != null && v !== '').join('/')
}
