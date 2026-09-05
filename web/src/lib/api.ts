import type { AgentPayload, Health, StreamEvent, Take, TakeEvent } from './types'

export class ApiError extends Error {
  status: number
  constructor(message: string, status = 0) {
    super(message)
    this.status = status
  }
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch {
    throw new ApiError('Cannot reach the SlateIQ API. Is the agent service running?')
  }
  if (!res.ok) throw new ApiError(`${init?.method ?? 'GET'} ${url} failed (${res.status})`, res.status)
  return (await res.json()) as T
}

export const getHealth = () => jsonFetch<Health>('/api/health')

/**
 * The backend answers `{count, source, takes:[...]}`; older mocks answer a bare
 * array. Accept both so one shape change cannot blank a whole screen.
 */
function unwrapList<T>(data: unknown, key: string): T[] {
  if (Array.isArray(data)) return data as T[]
  if (data && typeof data === 'object') {
    const v = (data as Record<string, unknown>)[key]
    if (Array.isArray(v)) return v as T[]
  }
  return []
}

/** Take rows arrive with ClickHouse-native names; normalise for the cards. */
function normaliseTake(raw: Record<string, unknown>): Take {
  return {
    ...(raw as unknown as Take),
    scene_number: (raw.scene_number ?? '') as Take['scene_number'],
    shot: String(raw.shot ?? ''),
    take_number: Number(raw.take_number ?? 0),
    status: String(raw.status ?? 'unknown') as Take['status'],
    flags: Array.isArray(raw.flags) ? (raw.flags as string[]) : [],
  }
}

export const getTakes = (scene?: string | number | null, opts?: { day?: number; limit?: number }) => {
  const p = new URLSearchParams()
  if (scene != null && scene !== '') p.set('scene', String(scene))
  if (opts?.day != null) p.set('day', String(opts.day))
  if (opts?.limit != null) p.set('limit', String(opts.limit))
  const qs = p.toString()
  return jsonFetch<unknown>(`/api/takes${qs ? `?${qs}` : ''}`).then((d) =>
    unwrapList<Record<string, unknown>>(d, 'takes').map(normaliseTake),
  )
}
export const getDpr = (day: number, refresh = false) =>
  jsonFetch<{ markdown: string; day: number; cached?: boolean; ran_query?: boolean }>(
    `/api/report/dpr?day=${day}${refresh ? '&refresh=1' : ''}`,
  )

/** Optional endpoint — degrade gracefully when the backend does not expose it. */
export async function getTakeEvents(takeId: string): Promise<TakeEvent[] | null> {
  try {
    const res = await fetch(`/api/take/${encodeURIComponent(takeId)}/events`)
    if (!res.ok) return null
    const data = (await res.json()) as unknown
    const rows = unwrapList<Record<string, unknown>>(data, 'events')
    if (!rows.length) return null
    // Backend rows are ClickHouse-shaped: t_offset_s / flag_type / severity.
    return rows.map((e) => ({
      t: Number(e.t ?? e.t_offset_s ?? 0),
      kind: String(e.kind ?? 'action'),
      speaker: (e.speaker as string) || undefined,
      text: (e.text as string) || undefined,
      flag: ((e.flag ?? e.flag_type) as string) || undefined,
      emotion: e.score != null ? Number(e.score) : undefined,
    }))
  } catch {
    return null
  }
}

export async function tts(text: string, signal?: AbortSignal): Promise<string> {
  const res = await fetch('/api/tts', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text }),
    signal,
  })
  if (!res.ok) throw new ApiError(`TTS failed (${res.status})`, res.status)
  const blob = await res.blob()
  return URL.createObjectURL(blob)
}

/**
 * POST /api/chat and consume the SSE stream.
 * Tolerates both `data: {...}` SSE framing and bare NDJSON lines.
 */
export async function streamChat(
  body: { session_id?: string; message: string },
  onEvent: (e: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json', accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok || !res.body) throw new ApiError(`Chat failed (${res.status})`, res.status)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  const emit = (raw: string) => {
    const payload = raw.startsWith('data:') ? raw.slice(5).trim() : raw.trim()
    if (!payload || payload === '[DONE]') return
    try {
      onEvent(JSON.parse(payload) as StreamEvent)
    } catch {
      /* ignore keepalives / comments */
    }
  }

  const flush = (final = false) => {
    let nl: number
    while ((nl = buf.indexOf('\n')) !== -1) {
      const line = buf.slice(0, nl).replace(/\r$/, '')
      buf = buf.slice(nl + 1)
      if (!line || line.startsWith(':') || /^(event|id|retry):/.test(line)) continue
      emit(line)
    }
    if (final && buf.trim()) emit(buf)
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    flush()
  }
  buf += decoder.decode()
  flush(true)
}

const FENCE = /```json\s*([\s\S]*?)```/gi

/** Pull the trailing ```json payload out of the agent's answer. */
export function extractPayload(text: string): { visible: string; payload?: AgentPayload } {
  let payload: AgentPayload | undefined
  let visible = text
  const matches = [...text.matchAll(FENCE)]
  for (const m of matches) {
    try {
      const parsed = JSON.parse(m[1]) as AgentPayload
      if (parsed && (Array.isArray(parsed.takes) || Array.isArray(parsed.sql))) {
        payload = {
          takes: Array.isArray(parsed.takes) ? parsed.takes : undefined,
          sql: Array.isArray(parsed.sql) ? parsed.sql.filter((s) => typeof s === 'string') : undefined,
        }
        visible = visible.replace(m[0], '')
      }
    } catch {
      /* not our block — leave it rendered as a normal code fence */
    }
  }
  return { visible: visible.trimEnd(), payload }
}
