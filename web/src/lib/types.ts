export type TakeStatus = 'circled' | 'ng' | 'hold' | string

/** Compact take reference emitted by the agent inside its final JSON block. */
export interface TakeRef {
  take_id: string
  clip_uri: string
  thumb_uri?: string
  scene_number: number
  shot: string
  take_number: number
  status: TakeStatus
  /** seek offset in seconds */
  t?: number
  /** optional extras the agent may include */
  summary?: string
  quality_score?: number
}

/** Full take record from GET /api/takes */
export interface Take extends TakeRef {
  duration_s?: number
  quality_score?: number
  flags?: string[]
  summary?: string
}

export interface TakeEvent {
  t: number
  kind: 'dialogue' | 'action' | 'flag' | string
  speaker?: string
  text?: string
  flag?: string
  emotion?: number
}

export interface Health {
  ok: boolean
  mcp: 'up' | 'down' | string
  clickhouse: 'up' | 'down' | string
}

export type StreamEvent =
  | { type: 'text'; delta: string }
  | { type: 'tool_call'; name: string; args?: { query?: string; [k: string]: unknown } }
  | { type: 'tool_result'; name: string; summary: string; rows?: number }
  | { type: 'agent'; name: string }
  | { type: 'final'; text: string; session_id: string }
  | { type: 'error'; message: string }

/** One entry in the live agent-trace panel. */
export interface TraceItem {
  id: string
  kind: 'agent' | 'tool_call' | 'tool_result' | 'error'
  name: string
  query?: string
  args?: Record<string, unknown>
  summary?: string
  rows?: number
  at: number
  pending?: boolean
}

export interface AgentPayload {
  takes?: TakeRef[]
  sql?: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  payload?: AgentPayload
  trace: TraceItem[]
  streaming?: boolean
  error?: string
}
