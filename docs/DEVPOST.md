# SlateIQ — Devpost submission text

> **Fill before submitting:** `HOSTED_URL`, `VIDEO_URL`. Every number below is a live query against the
> demo database — re-run `db/verify.py` if the dataset changes.

---

## Tagline

**A day of dailies, turned into a database you can ask questions of.** Gemini watches every take and
writes what it sees into ClickHouse; a Google Cloud Agent Builder crew answers the questions the
editor, the script supervisor, the 1st AD and the producer ask at 1 a.m. — through the official
ClickHouse MCP server, in SQL you can read.

---

## Inspiration

At 1 a.m., after a fourteen-hour day, three people on a film crew are still working.

The script supervisor is finishing the lined script and the facing pages — which setup covered which
line, which takes the director circled, where the boom dipped in. The production office is
reconciling the day's progress report: scenes shot, pages against plan, setups, wrap, overtime. And
tomorrow morning the assistant editor will sit down with two to four hours of dailies and watch all
of it, so that somebody in the cutting room knows what is in there.

Call it **three crew-hours per shooting day**. Over a thirty-day feature that is roughly **ninety
hours — about two crew-weeks, per production.** And at the end of it the knowledge lands in PDFs and
spreadsheets, where nobody can ask it anything.

The strange part is that a film set already generates beautifully structured data: takes, slates,
timecode, rolls, lenses, circled takes, continuity notes, camera and sound reports. It is a
time-series problem wearing a clipboard. So we gave a production a real analytical database — and
agents that both **fill** it from the raw footage and **answer** from it.

---

## What it does

SlateIQ is a production brain for a working shoot. Four things, one product.

**1 — Gemini watches the dailies.** Every clip goes to Gemini 3.5 Flash with a strict JSON schema:
transcript with speakers, action beats, quality flags (boom in shot, soft focus, line flub, audio
clipping, crew in shot, frame-edge drift), emotional intensity, and a circle-worthy recommendation.
In parallel, ffmpeg measures the clip itself at 25 Hz — focus, exposure, motion, audio peak in dBFS —
so every semantic judgement has an independent physical measurement sitting next to it. It all lands
in ClickHouse: **2,503 takes, 26,750 timestamped events, 120 scenes, 66 continuity notes, and
3,074,957 rows of frame telemetry** across a 30-day shoot.

**2 — You ask it things, in English.** A Google Cloud Agent Builder (ADK) network — a coordinator and
four specialists modelled on the four people who would actually open this at 10 p.m. — writes SQL and
runs it **through the official `mcp-clickhouse` MCP server at runtime**. The trace panel shows every
tool call, every query and every row count as it happens. No hidden database driver on the reasoning
path: the agents have exactly one data tool.

> *"Every take where Celia says 'forty years' — I need the timecode."* → the take, the line, the
> offset in seconds, and a player that seeks straight to it.
> *"Are we on schedule after day 12?"* → **48 4/8 pages shot of 52 planned. Three and a half pages
> behind — about half a day.** Days 8 and 11 lost setups to rain; it says so.

**3 — It catches what the humans missed.** This is the part no dailies tool can do today, because it
requires the semantic layer and the measured layer in the same query:

> *"Which circled takes are measurably soft?"*
> → **Scene 12, setup B, take 2 was circled — and it sits under the focus threshold for 13 seconds,
> averaging 0.52.** The director printed a soft take and nobody caught it.

That query joins Gemini's judgement against 3,074,957 rows of telemetry and comes back in **147 ms**.
That is why ClickHouse is in this product, and it is why the answer arrives before the producer has
finished asking.

**4 — It writes the paperwork.** The Daily Progress Report (scenes, pages in eighths, setups, takes,
circled, NG, print ratio, wrap and overtime) and the Editor's Log — the digital form of the script
supervisor's facing pages — generated entirely from live queries, in industry format, ready to paste
into an email. Gemini TTS reads the ninety-word version aloud for the drive home.

Day 12 of the demo shoot, generated end to end: *31 setups, 175 takes, 38 circled, 42 NG, 9 3/8 pages,
wrapped 15 minutes over.*

---

## Why this doesn't already exist

It half does, and it is worth being precise about which half.

- **Frame.io Camera to Cloud** and **Moxion** own *transport* — proxies and secure review within
  seconds of the cut. They move dailies brilliantly. They do not reason about them.
- **Strada** is the closest thing to us: AI auto-tagging, transcription, agents. But it searches
  *media*. It cannot tell you whether you are three and a half pages behind.
- **ScriptE** genuinely does produce a progress report and an editor report — from a script
  supervisor typing into forms all day. It answers the questions its forms were designed for.
- **Filmustage** answers questions in natural language, but about the *pre-production* breakdown.

Nobody joins the set-generated structured data to the media and opens both to analytical query.
That join is the whole product.

---

## How we built it

| Layer | What |
|---|---|
| **Reasoning** | **Google Cloud Agent Builder — Agent Development Kit (ADK) 2.8**, coordinator + `editor` / `production` / `continuity` / `report` specialists, `transfer_to_agent` routing |
| **Models** | **Gemini 3.5 Flash** — multimodal take analysis with a pydantic `response_schema`, and all agent reasoning; Gemini TTS for the spoken report |
| **Partner (ClickHouse track)** | **The official `mcp-clickhouse` MCP server**, StreamableHTTP, reached by a single shared ADK `McpToolset`. Every analytical answer in the product is SQL the agent wrote and executed through it. |
| **Store** | ClickHouse 25.6 — `take`, `take_event`, `take_analysis`, `continuity_note`, `frame_telemetry`, plus `AggregatingMergeTree` roll-ups behind `daily_progress` / `scene_progress` / `flag_summary` |
| **Google Cloud** | Cloud Run (agent API + React UI + Grafana, min-instances 0), Compute Engine e2-micro for the data plane, GCS for clips, Secret Manager, Artifact Registry, Cloud Build |
| **Front end** | React 18 + Vite + Tailwind — Ask (streaming chat + live MCP trace), Takes browser with a player that seeks to the flagged frame, Production Health, About |
| **Ingest** | ffmpeg scene detection and telemetry extraction, Gemini File API, disk-cached results committed to the repo |

**Guardrails, because SQL written by a model is still SQL.** A `before_tool_callback` on every
`run_query` enforces a single `SELECT`/`WITH` statement, rejects anything destructive or
`INTO OUTFILE`, and *appends or clamps* the `LIMIT` rather than bouncing the call — so the model
doesn't burn a round trip on a fixable mistake — then records the executed SQL for the trace. An
`after_tool_callback` truncates oversized results and tells the model to re-query more tightly.

**Evidence, not assertion.** `agent/evals/` runs 16 real questions across all five agents against the
real MCP server, records routing, every tool call, the SQL and the latency, and Gemini-judges each
answer against a per-question rubric. **The harness fails the run if any question marked
`must_query` produced an answer without touching MCP.** Results: [`agent/evals/last_run.md`](../agent/evals/last_run.md).

---

## Challenges we ran into

**ADK pins MCP SDK 1.x; `mcp-clickhouse` needs 2.x.** Unresolvable in one process. We split them: the
MCP server runs as its own containerised service reached over HTTP with a bearer token — which turned
out to be the correct production shape anyway, not a workaround.

**Making generated SQL trustworthy.** `db/SCHEMA.md` is a single contract file, re-read at runtime and
injected into every agent's instructions, so the model is never guessing at column names. Then the
SELECT-only guardrail, then the eval suite. The failure mode we cared most about was not a bad query —
it was a confident answer produced *without* one, so that is the one the harness hard-fails on.

**Fitting a 3M-row analytical database on a free-tier e2-micro.** 1 GiB of RAM, ClickHouse capped at
400 MiB per query, and the seed shipped in take-id-ranged Parquet chunks so peak memory stays bounded
regardless of table size. Total hosting cost: **$0** (see `deploy/cost.md`).

**Getting the vocabulary right.** Shooting ratio is *material shot vs. material in the finished cut* —
it is not takes divided by circled takes, which is a print ratio, and we say print ratio. 8/8 of a page
is written "1 page". The director circles a take; the script supervisor records it. Getting these
wrong is the fastest way to lose a room of film people.

---

## What we learned

That a shoot is an event-stream problem, and the moment you model it as one, questions that were
previously somebody's memory become one query. And that the interesting agent design decision was
*subtraction*: giving each specialist exactly one tool — the ClickHouse MCP toolset — made the
behaviour dramatically more reliable than giving them a toolbox.

---

## What's next

The full 2nd-AD Daily Production Report; camera and sound reports emitted per roll (the schema already
carries roll, sound roll, lens, fps, ISO and timecode); live ingest from camera cards on set; the lined
script reconstructed from coverage; Avid/Resolve bin and ALE export so circled takes land in the
cutting room without a human retyping them; per-production Grafana alerts on print ratio and overtime.

---

## Credits & licence

Demo dailies are cut from **Tears of Steel** © Blender Foundation, [mango.blender.org](https://mango.blender.org/),
licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). SlateIQ is not affiliated with the
Blender Foundation. All schedule, scene and telemetry data for the 30-day shoot is synthetic.
SlateIQ is open source under **Apache-2.0**.

**Try it:** `HOSTED_URL` · **Code:** https://github.com/kaitorecca/slateiq · **Video:** `VIDEO_URL`
