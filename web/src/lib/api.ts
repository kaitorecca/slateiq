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
    throw new ApiError('Cannot reach the SlateIQ API. Is the backend running on :8080?')
  }
  if (!res.ok) throw new ApiError(`${init?.method ?? 'GET'} ${url} failed (${res.status})`, res.status)
  return (await res.json()) as T
}

export const getHealth = () => jsonFetch<Health>('/api/health')
export const getTakes = (scene?: number | null) =>
  jsonFetch<Take[]>(scene == null ? '/api/takes' : `/api/takes?scene=${scene}`)
export const getDpr = (day: number) =>
  jsonFetch<{ markdown: string; day: number }>(`/api/report/dpr?day=${day}`)

/** Optional endpoint — degrade gracefully when the backend does not expose it. */
export async function getTakeEvents(takeId: string): Promise<TakeEvent[] | null> {
  try {
    const res = await fetch(`/api/take/${encodeURIComponent(takeId)}/events`)
    if (!res.ok) return null
    const data = (await res.json()) as unknown
    return Array.isArray(data) ? (data as TakeEvent[]) : null
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
