import { ArchDiagram } from '../components/ArchDiagram'
import { SlateMark } from '../components/Brand'
import { APP_URL, COMPLIANCE, GRAFANA_URL, MCP_HEALTH_URL, REPO_URL, SHOTS } from '../config'

const LIVE: Array<{ label: string; href: string; note: string }> = [
  { label: 'App (Cloud Run)', href: APP_URL, note: 'Agent + this UI, min-instances 0 — first hit is a cold start.' },
  { label: 'Grafana', href: GRAFANA_URL, note: 'The Production Health dashboard, same ClickHouse.' },
  { label: 'mcp-clickhouse health', href: MCP_HEALTH_URL, note: 'The official MCP server on the e2-micro VM.' },
  { label: 'Source', href: REPO_URL, note: 'Apache-2.0, public.' },
]

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      className="text-slate underline underline-offset-2 hover:text-ink"
      href={href}
      target="_blank"
      rel="noreferrer noopener"
    >
      {children}
    </a>
  )
}

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
          <div className="flex w-full shrink-0 flex-wrap items-center gap-2 sm:w-auto">
            <span className="chip border-slate/50 bg-slate/10 px-3 py-1.5 text-[11px] font-semibold text-slate">
              ClickHouse track
            </span>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer noopener"
              className="chip px-3 py-1.5 text-[11px] font-semibold transition hover:border-slate/50 hover:text-slate"
            >
              <svg viewBox="0 0 16 16" className="mr-1.5 h-3.5 w-3.5 fill-current" aria-hidden="true">
                <path d="M8 .2a8 8 0 0 0-2.53 15.59c.4.07.55-.17.55-.38l-.01-1.34c-2.23.49-2.7-1.07-2.7-1.07-.36-.93-.89-1.18-.89-1.18-.73-.5.06-.49.06-.49.8.06 1.23.83 1.23.83.72 1.23 1.88.87 2.34.67.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.96 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.08-1.87 3.76-3.65 3.96.29.25.54.73.54 1.48l-.01 2.19c0 .21.15.46.55.38A8 8 0 0 0 8 .2Z" />
              </svg>
              GitHub
            </a>
          </div>
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

        <section>
          <h2 className="label mb-3">Live</h2>
          <div className="card divide-y divide-line overflow-hidden">
            {LIVE.map((l) => (
              <div key={l.label} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3">
                <span className="w-full shrink-0 text-[12px] font-semibold text-ink sm:w-[170px]">{l.label}</span>
                <span className="min-w-0 flex-1 break-all font-mono text-[11.5px]">
                  <ExtLink href={l.href}>{l.href.replace(/^https?:\/\//, '')}</ExtLink>
                </span>
                <span className="w-full text-[11px] text-faint sm:w-auto sm:max-w-[42%]">{l.note}</span>
              </div>
            ))}
          </div>
          <p className="mt-2 px-1 text-[11px] text-faint">
            Hosted endpoints are build-time configuration (<span className="font-mono text-dim">VITE_APP_URL</span>,{' '}
            <span className="font-mono text-dim">VITE_GRAFANA_URL</span>,{' '}
            <span className="font-mono text-dim">VITE_MCP_HEALTH_URL</span>) and are recorded in{' '}
            <span className="font-mono text-dim">deploy/OUTPUT.md</span>. The VM's IP is ephemeral, so the MCP host can
            move between deploys.
          </p>
        </section>

        <section>
          <h2 className="label mb-3">Screens</h2>
          <div className="-mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-2">
            {SHOTS.map((sh) => (
              <figure
                key={sh.src}
                className="card w-[280px] shrink-0 snap-start overflow-hidden p-0 sm:w-[340px]"
              >
                <img
                  src={sh.src}
                  alt={sh.title}
                  loading="lazy"
                  decoding="async"
                  className="block h-[180px] w-full border-b border-line bg-cell object-cover object-top sm:h-[214px]"
                />
                <figcaption className="p-3">
                  <div className="text-[12px] font-semibold text-ink">{sh.title}</div>
                  <p className="mt-1 text-[11px] leading-relaxed text-dim">{sh.caption}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section>
          <h2 className="label mb-3">How it complies</h2>
          <div className="card divide-y divide-line overflow-hidden">
            {COMPLIANCE.map(([t, b]) => (
              <div key={t} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3">
                <span className="w-full shrink-0 text-[12px] font-semibold text-ink sm:w-[230px]">{t}</span>
                <p className="min-w-0 flex-1 text-[11.5px] leading-relaxed text-dim">{b}</p>
              </div>
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
