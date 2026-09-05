/**
 * Zero-dependency mock of the SlateIQ backend so the web app can be developed
 * without the agent/ FastAPI service running. Mirrors docs' API contract exactly.
 *   node mock/server.mjs      # listens on :8811 (MOCK_PORT to override)
 */
import http from 'node:http'
import { Buffer } from 'node:buffer'

const PORT = Number(process.env.MOCK_PORT || 8811)
const SCENES = [12, 27, 41, 63]
const SHOTS = ['A', 'B', 'C']
const FLAGS = ['soft_focus', 'boom_in_shot', 'audio_clip', 'flub', 'overlap', 'continuity']
const SUMMARIES = [
  'Celia crosses to the window on the line; performance settles by the midpoint, focus holds on the eyes throughout.',
  'Wide master. Boom dips into frame top-right around 00:07; usable up to the dolly move.',
  'Tight single. Strong emotional beat on "forty years"; slight soft focus as she leans back.',
  'Handheld push-in. Audio peaks hot on the shout; camera operator recovers frame quickly.',
  'Clean take, no technical issues. Director circled it on the floor.',
]

let idc = 0
const takes = []
for (const scene of SCENES) {
  for (let s = 0; s < 2; s++) {
    const shot = SHOTS[s % SHOTS.length]
    for (let n = 1; n <= 3; n++) {
      const i = idc++
      const status = n === 3 ? 'circled' : i % 5 === 0 ? 'ng' : i % 7 === 0 ? 'hold' : 'ng'
      const flags = status === 'circled' ? [] : FLAGS.slice(i % 3, (i % 3) + (i % 2 ? 2 : 1))
      takes.push({
        take_id: `T-${scene}${shot}-${n}`,
        scene_number: scene,
        shot,
        take_number: n,
        status,
        clip_uri: `clips/sc${scene}${shot}_t${n}.mp4`,
        thumb_uri: `clips/sc${scene}${shot}_t${n}.jpg`,
        duration_s: 24 + ((i * 7) % 40),
        quality_score: status === 'circled' ? 78 + (i % 20) : 30 + ((i * 13) % 45),
        flags,
        summary: SUMMARIES[i % SUMMARIES.length],
      })
    }
  }
}

const eventsFor = (id) => {
  const t = takes.find((x) => x.take_id === id)
  if (!t) return []
  const d = t.duration_s
  const out = []
  for (let i = 1; i < 6; i++) {
    out.push({
      t: Math.round((d * i) / 6),
      kind: 'dialogue',
      speaker: i % 2 ? 'CELIA' : 'THOM',
      text: i === 3 ? "It's been forty years. You still don't understand what you did." : 'Line of dialogue for this beat.',
      emotion: 0.3 + i * 0.1,
    })
  }
  for (const f of t.flags) out.push({ t: Math.round(d * (0.2 + Math.random() * 0.6)), kind: 'flag', flag: f })
  return out.sort((a, b) => a.t - b.t)
}

const DPR = (day) => `# Daily Progress Report — Day ${day}

**Production:** THE LONG WINTER · **Unit:** Main · **Location:** Stage 4 / Ext. Quarry

## Summary
Scheduled 4 1/8 pages across scenes 27, 41 and 63; **completed 3 6/8 pages**. Company moved once.
First shot 08:41 (call 07:30), camera wrap 19:12, company wrap 19:48 — **0:18 into overtime**.

## Scenes
| Scene | Planned | Shot | Takes | Circled | Status |
|---|---|---|---|---|---|
| 27 | 1 4/8 | 1 4/8 | 9 | 2 | Complete |
| 41 | 1 5/8 | 1 5/8 | 11 | 3 | Complete |
| 63 | 1 0/8 | 5/8 | 6 | 1 | **Incomplete — carry to Day ${day + 1}** |

## Notes
- Shooting ratio for the day: **5.3:1** (up from 4.1:1 running average).
- 4 takes flagged \`boom_in_shot\` in scene 41 — recommend a boom op note before the next stage day.
- Continuity: Celia's scarf is tied left in 41A-2 and right in 41A-4; 41A-4 is circled.

## Risk
At the current pace the shoot finishes **1.4 days over schedule**. Scenes 63 and 64 should be
considered for combination on the next quarry day.
`

const answers = {
  scene: {
    agents: ['coordinator', 'editor_agent'],
    sql: [
      "SELECT take_id, shot, take_number, status, quality_score, clip_uri FROM take WHERE scene_number = 27 AND status = 'circled' ORDER BY quality_score DESC LIMIT 5",
      'SELECT flag, count() AS n FROM take_event WHERE scene_number = 27 AND kind = \'flag\' GROUP BY flag ORDER BY n DESC',
    ],
    text: `Three takes stand out for **scene 27**.

- **27A-3** is the strongest overall: quality 92, clean audio, no flags, and the director circled it on the floor.
- **27B-3** is the best of the coverage — good for the reaction cut at 00:11.
- **27A-2** is a usable safety, but the boom dips into frame near the end.

Nine takes were rolled in total; two were circled, giving scene 27 a shooting ratio of 4.5:1.`,
  },
  schedule: {
    agents: ['coordinator', 'production_agent'],
    sql: [
      'SELECT day_number, sum(pages_planned) AS planned, sum(pages_shot) AS shot FROM shooting_day WHERE day_number <= 12 GROUP BY day_number ORDER BY day_number',
      'SELECT scene_number, count() AS takes, countIf(status = \'circled\') AS circled FROM take GROUP BY scene_number ORDER BY takes DESC LIMIT 10',
    ],
    text: `After **day 12** you are **1.4 days behind** a 30-day board.

- Pages: **46 2/8 planned**, **42 5/8 shot** (92%).
- Running shooting ratio 4.8:1, trending up over the last three days.
- Scenes 63 and 64 are the schedule risk — both are quarry exteriors with a weather window.

Overtime has been incurred on 5 of the last 7 days, averaging 22 minutes.`,
  },
  default: {
    agents: ['coordinator', 'editor_agent'],
    sql: [
      "SELECT t.take_id, t.scene_number, t.shot, t.take_number, t.status, t.clip_uri, e.t AS offset FROM take_event e JOIN take t ON t.take_id = e.take_id WHERE e.kind = 'dialogue' AND positionCaseInsensitive(e.text, 'forty years') > 0 ORDER BY t.scene_number LIMIT 10",
    ],
    text: `Found **3 takes** where that line is spoken. The strongest reading is in scene 41 — the pause before "forty years" is a full beat longer than in the other two.`,
  },
}

function pick(msg) {
  const m = msg.toLowerCase()
  if (/schedule|day \d|dpr|progress report/.test(m)) return answers.schedule
  if (/scene\s*\d/.test(m)) return answers.scene
  return answers.default
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function wavBeep(seconds = 2.4) {
  const rate = 22050
  const n = Math.floor(rate * seconds)
  const buf = Buffer.alloc(44 + n * 2)
  buf.write('RIFF', 0)
  buf.writeUInt32LE(36 + n * 2, 4)
  buf.write('WAVEfmt ', 8)
  buf.writeUInt32LE(16, 16)
  buf.writeUInt16LE(1, 20)
  buf.writeUInt16LE(1, 22)
  buf.writeUInt32LE(rate, 24)
  buf.writeUInt32LE(rate * 2, 28)
  buf.writeUInt16LE(2, 32)
  buf.writeUInt16LE(16, 34)
  buf.write('data', 36)
  buf.writeUInt32LE(n * 2, 40)
  for (let i = 0; i < n; i++) {
    const env = Math.min(1, i / 2000) * Math.max(0, 1 - i / n)
    const v = Math.sin((2 * Math.PI * 210 * i) / rate) * 0.22 * env
    buf.writeInt16LE(Math.round(v * 32767), 44 + i * 2)
  }
  return buf
}

const json = (res, obj, code = 200) => {
  const body = JSON.stringify(obj)
  res.writeHead(code, { 'content-type': 'application/json', 'access-control-allow-origin': '*' })
  res.end(body)
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x')
  const p = url.pathname
  res.setHeader('access-control-allow-origin', '*')
  if (req.method === 'OPTIONS') {
    res.writeHead(204, { 'access-control-allow-headers': '*', 'access-control-allow-methods': '*' })
    return res.end()
  }

  if (p === '/api/health') return json(res, { ok: true, mcp: 'up', clickhouse: 'up' })

  if (p === '/api/takes') {
    const scene = url.searchParams.get('scene')
    const out = scene ? takes.filter((t) => String(t.scene_number) === scene) : takes
    return json(res, out)
  }

  const ev = p.match(/^\/api\/take\/([^/]+)\/events$/)
  if (ev) return json(res, eventsFor(decodeURIComponent(ev[1])))

  if (p === '/api/report/dpr') {
    const day = Number(url.searchParams.get('day') || 12)
    await sleep(700)
    return json(res, { markdown: DPR(day), day })
  }

  if (p === '/api/tts' && req.method === 'POST') {
    await sleep(500)
    const wav = wavBeep()
    res.writeHead(200, { 'content-type': 'audio/wav', 'content-length': wav.length })
    return res.end(wav)
  }

  if (p === '/api/chat' && req.method === 'POST') {
    let body = ''
    for await (const c of req) body += c
    let message = ''
    try {
      message = JSON.parse(body).message ?? ''
    } catch {}
    const a = pick(message)

    res.writeHead(200, {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache',
      connection: 'keep-alive',
      'x-accel-buffering': 'no',
    })
    const send = (o) => res.write(`data: ${JSON.stringify(o)}\n\n`)

    send({ type: 'agent', name: a.agents[0] })
    await sleep(320)
    send({ type: 'agent', name: a.agents[1] })
    await sleep(220)
    for (const q of a.sql) {
      send({ type: 'tool_call', name: 'run_query', args: { query: q } })
      await sleep(650)
      const rows = 3 + Math.floor(Math.random() * 900)
      send({ type: 'tool_result', name: 'run_query', summary: `Returned ${rows} rows in ${(Math.random() * 40 + 6).toFixed(1)} ms`, rows })
      await sleep(240)
    }

    const withTakes = takes.filter((t) => t.status === 'circled').slice(0, 3)
    const payload = {
      takes: withTakes.map((t, i) => ({
        take_id: t.take_id,
        clip_uri: t.clip_uri,
        thumb_uri: t.thumb_uri,
        scene_number: t.scene_number,
        shot: t.shot,
        take_number: t.take_number,
        status: t.status,
        t: 4 + i * 6,
      })),
      sql: a.sql,
    }
    const full = `${a.text}\n\n\`\`\`json\n${JSON.stringify(payload, null, 2)}\n\`\`\``

    for (const tok of a.text.match(/\S+\s*/g) ?? []) {
      send({ type: 'text', delta: tok })
      await sleep(18)
    }
    await sleep(150)
    send({ type: 'final', text: full, session_id: 'mock-session-1' })
    return res.end()
  }

  if (p.startsWith('/clips/')) {
    res.writeHead(404, { 'content-type': 'text/plain' })
    return res.end('no clip in mock mode')
  }

  json(res, { error: 'not found', path: p }, 404)
})

server.listen(PORT, () => {
  console.log(`[mock] SlateIQ API on http://localhost:${PORT}`)
})
