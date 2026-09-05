import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { extractPayload, streamChat } from '../lib/api'
import type { ChatMessage, StreamEvent, TraceItem } from '../lib/types'
import { AgentTrace } from '../components/AgentTrace'
import { Markdown } from '../components/Markdown'
import { SqlBlock } from '../components/SqlBlock'
import { TakeCard } from '../components/TakeCard'
import { ErrorBox, Spinner } from '../components/States'
import { SlateMark } from '../components/Brand'

const CHIPS = [
  'Best takes for scene 27?',
  'Are we on schedule after day 12?',
  "Every take where Celia says 'forty years'",
  'Takes with boom in shot today',
  'Continuity issues in scene 41',
  "Write today's Daily Progress Report",
]

let seq = 0
const uid = () => `${Date.now().toString(36)}-${(seq += 1)}`

const fmtSecs = (ms: number) => (ms < 10_000 ? (ms / 1000).toFixed(1) : Math.round(ms / 1000).toString())

/** Live wall-clock while the agent is still working. */
function Elapsed({ since }: { since?: number }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (since == null) return
    const id = window.setInterval(() => setNow(Date.now()), 100)
    return () => window.clearInterval(id)
  }, [since])
  if (since == null) return null
  return (
    <span className="font-mono tabular-nums text-[11px] text-faint" aria-live="off">
      {fmtSecs(Math.max(0, now - since))}s
    </span>
  )
}

/** "3 queries · 812 rows · 21.4 s" -- what the answer actually cost. */
function AnswerStats({ m }: { m: ChatMessage }) {
  const queries = m.trace.filter((t) => t.kind === 'tool_call' && t.query).length
  const rows = m.trace.reduce((n, t) => n + (t.rows != null && t.rows > 0 ? t.rows : 0), 0)
  if (!queries && m.elapsedMs == null) return null
  return (
    <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 pt-0.5 font-mono text-[10.5px] text-faint">
      <span>
        {queries} quer{queries === 1 ? 'y' : 'ies'}
      </span>
      <span aria-hidden="true">·</span>
      <span>{rows.toLocaleString()} rows</span>
      {m.elapsedMs != null && (
        <>
          <span aria-hidden="true">·</span>
          <span>{fmtSecs(m.elapsedMs)} s</span>
        </>
      )}
      <span aria-hidden="true">·</span>
      <span className="text-faint/80">through mcp-clickhouse</span>
    </div>
  )
}

function AssistantBubble({ m }: { m: ChatMessage }) {
  const { visible, payload } = useMemo(() => extractPayload(m.text), [m.text])
  // The `final` SSE event carries the same takes already enriched by the
  // backend with scene / shot / take / status / thumbnail from ClickHouse --
  // prefer it over re-parsing the model's own fenced block, which only ever
  // carries take_id + clip_uri.
  const takes = m.payload?.takes?.length ? m.payload.takes : payload?.takes ?? []
  const sql = m.payload?.sql?.length ? m.payload.sql : payload?.sql ?? []

  return (
    <div className="flex gap-3">
      <div className="mt-0.5 shrink-0">
        <SlateMark className="h-7 w-7" />
      </div>
      <div className="min-w-0 flex-1 space-y-3">
        {visible ? (
          <Markdown>{visible}</Markdown>
        ) : m.streaming ? (
          <div className="flex items-center gap-2 text-[13px] text-faint">
            <Spinner className="h-3.5 w-3.5" />
            <span className="animate-blip">consulting the dailies…</span>
            <Elapsed since={m.startedAt} />
          </div>
        ) : null}
        {m.streaming && visible && (
          <span className="flex items-center gap-2">
            <span className="inline-block h-3.5 w-[7px] animate-blip bg-slate/80" aria-hidden="true" />
            <Elapsed since={m.startedAt} />
          </span>
        )}

        {takes.length > 0 && (
          <div>
            <div className="label mb-2">{takes.length} take{takes.length > 1 ? 's' : ''}</div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {takes.map((t, i) => (
                <TakeCard key={`${t.take_id}-${i}`} take={t} compact />
              ))}
            </div>
          </div>
        )}

        {sql.length > 0 && (
          <details className="group rounded-xl border border-line bg-panel/50">
            <summary className="cursor-pointer list-none px-3 py-2 text-[11px] font-semibold uppercase tracking-[.14em] text-faint transition hover:text-dim">
              <span className="inline-block transition group-open:rotate-90">›</span> SQL run through MCP ({sql.length})
            </summary>
            <div className="space-y-2 p-2 pt-0">
              {sql.map((q, i) => (
                <SqlBlock key={i} sql={q} dense />
              ))}
            </div>
          </details>
        )}

        {!m.streaming && <AnswerStats m={m} />}

        {m.error && <ErrorBox message={m.error} />}
      </div>
    </div>
  )
}

export function Ask() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [traceOpen, setTraceOpen] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const taRef = useRef<HTMLTextAreaElement | null>(null)

  const trace = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === 'assistant') return messages[i].trace
    return []
  }, [messages])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  useEffect(() => () => abortRef.current?.abort(), [])

  const send = useCallback(
    async (text: string) => {
      const q = text.trim()
      if (!q || busy) return
      setInput('')
      setBusy(true)
      const aId = uid()
      setMessages((m) => [
        ...m,
        { id: uid(), role: 'user', text: q, trace: [] },
        { id: aId, role: 'assistant', text: '', trace: [], streaming: true, startedAt: Date.now() },
      ])

      const patch = (fn: (m: ChatMessage) => ChatMessage) =>
        setMessages((ms) => ms.map((m) => (m.id === aId ? fn(m) : m)))

      const ac = new AbortController()
      abortRef.current = ac

      const onEvent = (e: StreamEvent) => {
        switch (e.type) {
          case 'text':
            patch((m) => ({ ...m, text: m.text + (e.delta ?? '') }))
            break
          case 'agent':
            patch((m) =>
              m.trace.at(-1)?.kind === 'agent' && m.trace.at(-1)?.name === e.name
                ? m
                : { ...m, trace: [...m.trace, { id: uid(), kind: 'agent', name: e.name, at: Date.now() }] },
            )
            break
          case 'tool_call': {
            const item: TraceItem = {
              id: uid(),
              kind: 'tool_call',
              name: e.name,
              query: typeof e.args?.query === 'string' ? e.args.query : undefined,
              args: e.args && typeof e.args.query !== 'string' ? (e.args as Record<string, unknown>) : undefined,
              at: Date.now(),
              pending: true,
            }
            patch((m) => ({ ...m, trace: [...m.trace, item] }))
            break
          }
          case 'tool_result':
            patch((m) => {
              const trace = [...m.trace]
              for (let i = trace.length - 1; i >= 0; i--) {
                if (trace[i].kind === 'tool_call' && trace[i].name === e.name && trace[i].pending) {
                  trace[i] = { ...trace[i], pending: false, summary: e.summary, rows: e.rows }
                  return { ...m, trace }
                }
              }
              return {
                ...m,
                trace: [
                  ...trace,
                  { id: uid(), kind: 'tool_result', name: e.name, summary: e.summary, rows: e.rows, at: Date.now() },
                ],
              }
            })
            break
          case 'final':
            if (e.session_id) setSessionId(e.session_id)
            patch((m) => ({
              ...m,
              text: e.text || m.text,
              payload: {
                takes: Array.isArray(e.takes) && e.takes.length ? e.takes : m.payload?.takes,
                sql: Array.isArray(e.sql) && e.sql.length ? e.sql : m.payload?.sql,
              },
              streaming: false,
            }))
            break
          case 'error':
            patch((m) => ({ ...m, error: e.message, streaming: false }))
            break
        }
      }

      try {
        await streamChat({ session_id: sessionId, message: q }, onEvent, ac.signal)
        patch((m) => ({
          ...m,
          streaming: false,
          elapsedMs: m.startedAt ? Date.now() - m.startedAt : m.elapsedMs,
          trace: m.trace.map((t) => ({ ...t, pending: false })),
          error: m.text || m.error ? m.error : 'The agent returned no answer.',
        }))
      } catch (err: unknown) {
        const stop = (m: ChatMessage): ChatMessage => ({
          ...m,
          streaming: false,
          elapsedMs: m.startedAt ? Date.now() - m.startedAt : m.elapsedMs,
        })
        if ((err as Error)?.name === 'AbortError') patch(stop)
        else patch((m) => ({ ...stop(m), error: err instanceof Error ? err.message : String(err) }))
      } finally {
        setBusy(false)
        abortRef.current = null
      }
    },
    [busy, sessionId],
  )

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send(input)
    }
  }

  return (
    <div className="flex h-full min-h-0">
      {/* conversation */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
          <div className="mx-auto w-full max-w-3xl space-y-8">
            {messages.length === 0 && (
              <div className="animate-rise space-y-6 pt-6">
                <div>
                  <div className="clapper mb-5 h-[7px] w-24 opacity-70" />
                  <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-ink sm:text-[32px]">
                    Ask the dailies.
                  </h1>
                  <p className="mt-2 max-w-xl text-[13.5px] leading-relaxed text-dim">
                    Every take, line, flag and frame from the shoot lives in ClickHouse. The Gemini multi-agent crew
                    writes the SQL, runs it through the official ClickHouse MCP server, and answers with the clips.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {CHIPS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => void send(c)}
                      className="chip px-3 py-1.5 text-[12px] hover:border-slate/50 hover:bg-slate/10 hover:text-slate"
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) =>
              m.role === 'user' ? (
                <div key={m.id} className="flex justify-end">
                  <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md border border-line bg-raise px-4 py-2.5 text-[13.5px] leading-relaxed text-ink">
                    {m.text}
                  </p>
                </div>
              ) : (
                <AssistantBubble key={m.id} m={m} />
              ),
            )}
          </div>
        </div>

        {/* composer */}
        <div className="border-t border-line bg-cell/70 px-4 py-3 backdrop-blur sm:px-8">
          <div className="mx-auto w-full max-w-3xl">
            {messages.length > 0 && (
              <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
                {CHIPS.slice(0, 4).map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => void send(c)}
                    disabled={busy}
                    className="chip shrink-0 whitespace-nowrap px-2.5 py-1 text-[11px] hover:border-slate/50 hover:text-slate disabled:opacity-40"
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
            <div className="flex items-end gap-2 rounded-xl border border-line bg-panel px-3 py-2 transition focus-within:border-slate/50">
              <textarea
                ref={taRef}
                id="ask-input"
                name="question"
                rows={1}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  const el = e.target
                  el.style.height = 'auto'
                  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
                }}
                onKeyDown={onKeyDown}
                placeholder="Ask about takes, coverage, continuity, schedule…"
                aria-label="Ask the dailies"
                className="max-h-40 min-h-[28px] flex-1 resize-none bg-transparent py-1 text-[13.5px] leading-relaxed text-ink placeholder:text-faint focus:outline-none"
              />
              {busy ? (
                <button className="btn h-9 px-3 py-0" onClick={() => abortRef.current?.abort()}>
                  <Spinner className="h-3.5 w-3.5" /> Stop
                </button>
              ) : (
                <button
                  className="btn btn-primary h-9 px-3 py-0"
                  onClick={() => void send(input)}
                  disabled={!input.trim()}
                  aria-label="Send question"
                >
                  Ask
                  <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor" aria-hidden="true">
                    <path d="M1.5 14.5 15 8 1.5 1.5 4 8l-2.5 6.5ZM4 8h11" stroke="currentColor" strokeWidth="1.2" fill="none" />
                  </svg>
                </button>
              )}
            </div>
            <div className="mt-1.5 flex items-center justify-between px-1 text-[10.5px] text-faint">
              <span>Enter to send · Shift+Enter for a new line</span>
              <button
                className="underline-offset-2 hover:text-dim hover:underline xl:hidden"
                onClick={() => setTraceOpen(true)}
              >
                View agent trace ({trace.length})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* trace panel — docked on wide screens */}
      <aside className="hidden w-[400px] shrink-0 border-l border-line bg-cell/60 xl:block 2xl:w-[460px]">
        <AgentTrace items={trace} live={busy} />
      </aside>

      {traceOpen && (
        <div className="fixed inset-0 z-50 flex justify-end xl:hidden" role="dialog" aria-modal="true" aria-label="Agent trace">
          <div className="absolute inset-0 bg-black/65" onClick={() => setTraceOpen(false)} />
          <div className="relative flex h-full w-full max-w-[440px] animate-rise flex-col border-l border-line bg-cell">
            <button
              className="btn absolute right-3 top-2.5 z-10 h-7 px-2 py-0 text-[11px]"
              onClick={() => setTraceOpen(false)}
            >
              Close
            </button>
            <AgentTrace items={trace} live={busy} />
          </div>
        </div>
      )}
    </div>
  )
}
