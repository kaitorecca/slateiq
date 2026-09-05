import { ArchDiagram } from '../components/ArchDiagram'
import { SlateMark } from '../components/Brand'

const STACK = [
  ['Gemini 3.5 Flash', 'Multimodal analysis of every take: dialogue, action, emotion, QC flags — structured JSON.'],
  ['Google ADK', 'Coordinator + four specialist sub-agents (editor, production, continuity, report).'],
  ['ClickHouse', 'The production brain: takes, timestamped events, continuity notes, frame-level telemetry.'],
  ['mcp-clickhouse', 'The official MCP server. Every analytical answer is SQL the agent wrote and ran through it — live.'],
  ['Gemini TTS', 'Reads the Daily Progress Report aloud for the drive home.'],
  ['Cloud Run + GCS', 'Agent, UI and Grafana on Cloud Run (min-instances 0); clips served from GCS.'],
]

function Card({ title, body }: { title: string; body: string }) {
  return (
    <div className="card p-4">
      <h3 className="text-[13px] font-semibold text-ink">{title}</h3>
      <p className="mt-1.5 text-[12px] leading-relaxed text-dim">{body}</p>
    </div>
  )
}

export function About() {
  return (
    <div className="h-full overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto w-full max-w-[1100px] space-y-8 pb-12">
        <header className="flex flex-wrap items-start gap-5">
          <SlateMark className="h-12 w-12" />
          <div className="min-w-0 flex-1">
            <div className="clapper mb-3 h-[7px] w-16 opacity-70" />
            <h1 className="text-2xl font-semibold tracking-tight text-ink">SlateIQ</h1>
            <p className="mt-1.5 max-w-2xl text-[13.5px] leading-relaxed text-dim">
              A day of raw dailies becomes a queryable production brain. Gemini watches every take and writes
              structured, timestamped knowledge into ClickHouse; a Google ADK agent network answers the questions
              editors, script supervisors, 1st ADs and producers ask every night — and writes the documents that are
              otherwise typed by hand at 1 a.m.
            </p>
          </div>
          <span className="chip border-slate/50 bg-slate/10 px-3 py-1.5 text-[11px] font-semibold text-slate">
            ClickHouse track
          </span>
        </header>

        <section className="card overflow-hidden">
          <header className="flex items-center gap-2 border-b border-line px-4 py-3">
            <h2 className="text-[13px] font-semibold text-ink">Architecture</h2>
            <span className="chip ml-auto px-2 py-[2px] text-[10px]">Gemini → ADK → mcp-clickhouse → ClickHouse</span>
          </header>
          <div className="overflow-x-auto p-4">
            <div className="min-w-[720px]">
              <ArchDiagram />
            </div>
          </div>
        </section>

        <section>
          <h2 className="label mb-3">Stack</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {STACK.map(([t, b]) => (
              <Card key={t} title={t} body={b} />
            ))}
          </div>
        </section>

        <section className="card p-5">
          <h2 className="text-[13px] font-semibold text-ink">Footage attribution</h2>
          <p className="mt-2 max-w-3xl text-[12.5px] leading-relaxed text-dim">
            Demo dailies are cut from{' '}
            <a
              className="text-slate underline underline-offset-2"
              href="https://mango.blender.org/"
              target="_blank"
              rel="noreferrer noopener"
            >
              Tears of Steel
            </a>{' '}
            © copyright Blender Foundation |{' '}
            <a
              className="text-slate underline underline-offset-2"
              href="https://mango.blender.org/"
              target="_blank"
              rel="noreferrer noopener"
            >
              mango.blender.org
            </a>
            , licensed{' '}
            <a
              className="text-slate underline underline-offset-2"
              href="https://creativecommons.org/licenses/by/3.0/"
              target="_blank"
              rel="noreferrer noopener"
            >
              CC BY 3.0
            </a>
            . Clips were split by scene detection and some were deliberately degraded (blur, gain, crop) to create
            realistic QC variety — soft focus, audio clipping, boom in shot. No footage is presented as belonging to a
            real production.
          </p>
          <p className="mt-3 text-[11.5px] text-faint">
            SlateIQ is licensed Apache-2.0. Built for the Agentic Cinema Hackathon.
          </p>
        </section>
      </div>
    </div>
  )
}
