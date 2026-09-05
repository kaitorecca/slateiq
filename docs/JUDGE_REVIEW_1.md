# Judge Review #1 — SlateIQ

*Written as an unsympathetic Devpost judge for "Agentic Cinema: The Blockbuster Hackathon"
(Google Cloud; ClickHouse partner track), scoring **what exists today, 5 Sep**, not what is planned.
Docs-only review — no code was modified.*

**Context:** ~9,500 registrants; ClickHouse track prizes $7,500 / $4,500 / $3,000. The project gallery is
**unpublished**, so there is no read on competing ClickHouse entries — assume the field is strong and that
the differentiator has to be legible in the first 30 seconds, not discovered.

---

## (a) Scorecard — as a tough judge would score it today

| Criterion | Score | The single biggest reason |
|---|:--:|---|
| **Technological Implementation** (Google Cloud + partner) | **4 / 5** | The architecture is the real thing, not a veneer: a five-agent ADK network whose *only* data path is the official `mcp-clickhouse` server, a SELECT-only `before_tool_callback` that rewrites and clamps LIMITs, Gemini 3.5 Flash multimodal ingest with a pydantic `response_schema`, 3.07M telemetry rows. **But not one byte of runtime evidence is committed or reachable.** `agent/README.md` links to `evals/last_run.md`, which does not exist. There is no Cloud Run service. The hosted MCP endpoint answers `ERROR. ClickHouse connection failed.` A judge who clicks the link today sees a 503, and a judge who reads the repo has to take the MCP claim on faith. |
| **Design** (complete, coherent product) | **4 / 5** | This is a *product*, not a chat box: ingest → structured knowledge → ask → browse takes with a clip that seeks to the flagged frame → generated documents → spoken summary, in a coherent dark cutting-room language that uses real crew vocabulary (circled, NG, setups, slate, wrap). It loses the point on the front door: **there is no root `README.md` at all**, no screenshots anywhere, and the Production Health screen's Grafana story is conditional on an env var nobody can verify. The first 30 seconds of a judge's visit are currently a bare GitHub file listing. |
| **Potential Impact** (real problem, real audience) | **3 / 5** | The problem is correctly chosen and the four personas are the right four. But the pitch never converts that into a number. "Typed by hand at 1 a.m." is a mood; **nothing anywhere states how many hours this saves, for whom, at what day-rate, over how long a shoot** — and there is no acknowledgement that Frame.io C2C, Moxion and ScriptE already own parts of this workflow. Right now a judge hears "this would be useful" rather than "this removes ~3 crew-hours from every shooting day." |
| **Quality of the Idea** (creative, non-obvious) | **4 / 5** | The reframing is genuinely non-obvious and it is *earned*: treating a shoot as an event/time-series problem is what makes ClickHouse the correct tool rather than a sponsor tax, and the closed loop — Gemini **writes** the rows that ClickHouse later **answers** from — is a real idea. It stops short of 5 because the surface presentation still reads as "chat with your database", the single most common hackathon shape, and the one thing no incumbent can do (joining Gemini's *semantic* judgement against *measured* frame telemetry) is buried in a SQL appendix instead of being the headline. |

**Composite today: 15/20.** Every missing point is recoverable in under a day, and three of the four are recoverable in words rather than code.

---

## (b) Top 10 improvements, ranked by score-gain per hour

| # | Change | Est. | Criterion | Why it moves a judge |
|:--:|---|:--:|---|---|
| **1** | **Fix the hosted data plane and ship the Cloud Run URL.** `https://<vm>.sslip.io/health` currently returns `ERROR. ClickHouse connection failed.` while ClickHouse itself answers on `/`. That is almost certainly the `slateiq_ro` user/password or the container-internal host in the compose env, not the data. Fix, re-run `seed_remote.sh` if empty, then `deploy/cloudrun/deploy_agent.sh`, and record the URL in `deploy/OUTPUT.md`. | 0.5–1 h | **Stage 1 gate** | Without a working hosted URL nothing else is scored. This is the only item on the list that can cost the whole submission. |
| **2** | **Write a root `README.md`.** There isn't one. Above the fold: one-sentence pitch, the hosted URL, the 3-min video, a screenshot of the Ask screen with the trace panel open, the four-box architecture line `Gemini → ADK → mcp-clickhouse → ClickHouse`, a `curl -N /api/chat` one-liner, "ClickHouse track", Apache-2.0, and the *Tears of Steel* CC-BY credit. Then a 60-second quickstart. | 0.75 h | Design, Tech | It is the first artifact every judge opens and it is currently empty. Highest ratio on the list. |
| **3** | **Run the evals and commit `agent/evals/last_run.md`.** 16 questions, real coordinator, real MCP. Put the headline in the README: *"16/16 questions answered through `mcp-clickhouse`; 0 answered without a query; Gemini-judge mean X.X/5; median latency Y s."* | 0.75 h | Tech, Impact | This is the single most credible artifact you can produce, it converts "trust me, MCP is at runtime" into a number, and the README already links to it — so the link is **broken today**, which reads worse than not linking at all. |
| **4** | **Quantify the impact, with arithmetic on screen.** Use a defensible chain, not a big round number: script supervisor's daily paperwork (lined script + facing pages + daily reports) ≈ 45–90 min after wrap; production office DPR reconciliation ≈ 30–60 min; assistant editor sync-and-log pass over 2–4 h of dailies ≈ 2–3 h. Call it **≈3 crew-hours per shooting day → ≈90 hours over a 30-day shoot → roughly two crew-weeks per production.** Show the three numbers adding up. | 0.5 h | **Impact** | Judges reward *visible arithmetic* far more than the size of the result. This is the fastest point on the board — it is pure wording. |
| **5** | **Fix the shooting-ratio definition.** Everywhere in the project (`db/SCHEMA.md`, `slateiq_agent/prompts.py`, the DPR template) shooting ratio is defined as `takes / circled`. In the industry, **shooting ratio is the ratio of material *shot* to material in the *finished cut*** (e.g. 10:1). `takes / circled` is a real and useful metric, but its name is **print ratio** or **takes per print**. Rename it; compute a true shooting ratio from `sum(duration_s) / sum(duration_s where circled)`, which your data already supports. | 0.5 h | **Tech, Idea** | A working 1st AD or post supervisor on the judging panel spots this in one glance, and it instantly devalues every other correct term in the product. Cheapest credibility repair available. |
| **6** | **Make the MCP proof unmissable — a 5-second full-screen hold on the trace.** Tool name `run_query`, the server label `mcp-clickhouse`, the generated SQL, the row count, the latency. Mirror it in the README as a verbatim pasted trace block, and add the raw `curl -N -X POST .../api/chat` next to it so a judge can reproduce it in 10 seconds. | 0.5 h | **Tech** (Stage 1) | "Partner used at runtime" is a pass/fail gate. Do not make a judge infer it from an architecture diagram — show the tool call. |
| **7** | **Lead the demo with the one query no competitor can answer.** You have it and it is spectacular: `TOS-D12-S12-B-02-B` is a **circled** take that measures **13 seconds under the focus threshold**, average focus 0.521 — the director printed a soft take and nobody caught it. That query joins Gemini's semantic circling against 3M rows of independently measured telemetry and returns in **147 ms**. Put it at 0:45, not in an appendix. | 1 h | **Idea, Impact, Tech** | It answers "why Gemini *and* ClickHouse in one product" in a single shot, it is a catch worth real money on a real set, and it makes the 3M-row table load-bearing instead of decorative. |
| **8** | **Rewrite the Devpost opening to lead with the 1 a.m. scene and the number, not the stack.** The current "Inspiration" opens with an abstraction about structured data. Open on a person, a time, and a cost. Stack goes below the fold. *(Done — see `docs/DEVPOST.md`.)* | 0.5 h | Impact, Idea | The first 40 words decide whether the rest gets read carefully. |
| **9** | **Add a "Why not Frame.io / Moxion / Strada / ScriptE" paragraph — accurately.** Frame.io C2C and Moxion own *transport* (proxies and review, seconds after the cut). **Strada** (Michael Cioni, ex-Frame.io) is your closest competitor and must be named: AI auto-tagging, transcription and "Strada Agents" — but it searches *media*, it does not reason over production numbers. **ScriptE does already generate a Daily Progress Report and an editor report** — do not claim otherwise; its input is a script supervisor typing, and it cannot answer a question it has no form for. Filmustage's "AI Dude" does NL, but over *pre-production breakdown*, not dailies. **The gap that actually holds: nobody joins set-generated structured data to the media and exposes both to analytical NL query.** Avoid "first cloud dailies" and "first AI tagging" — both are already taken. | 0.5 h | **Impact, Idea** | Naming your incumbents *correctly* is the cheapest signal of domain credibility. Overclaiming against ScriptE or Strada in front of a judge who knows them is worse than saying nothing. |
| **10** | **Two screenshots and one 6-second GIF** — Ask + trace panel, Takes drawer with the flag timeline — in the README and on the About screen. | 0.5 h | Design | Most judges triage on images before they read a word. Costs nothing, and the UI is already good enough to sell itself. |

### Terminology audit — what a script supervisor would flag

| Term | Status | Fix |
|---|---|---|
| **Shooting ratio = takes / circled** | ✗ **Wrong** | Shooting ratio is *material shot : material in the finished cut*. Rename to **print ratio** / **takes per print**; derive a real shooting ratio from durations. Fix in `db/SCHEMA.md`, `prompts.py` (SQL_RULES + production playbook), the DPR template. |
| **"Daily Progress Report" = DPR** | ⚠ **Two different documents** | **DPR is the Daily Production Report**, compiled by the **2nd AD** — the counterpart to the call sheet, covering crew, cast times, hours, meals, film/media, as well as scenes and pages. The **Daily Progress Report** is a narrower document from the script supervisor / AD dept: scenes shot, added, deleted, setups, page counts. Your template (call, wrap, scenes, pages, setups, takes, circled, NG) is genuinely a **Progress Report** — but you label it DPR, which reads as the Production Report. Cleanest fix: **call the document what it is** — "Daily Progress Report" — and say plainly in the pitch that it is the script-supervisor-side report, with the full 2nd-AD Production Report as a "what's next". Do not silently equate them. |
| **Circled takes** | ✓ Correct | Attribute it precisely: **the director designates** the preferred take; the **script supervisor records and circles it**, and it is marked on the **camera and sound reports** so dailies and editorial prioritise it. Do not say the script supervisor chooses them. One clause in the VO buys real credibility. |
| **Editor's Log / circled-take list** | ✓ Close | This is the digital form of the script supervisor's **facing pages** and daily editor log. Say so once — it names the paper document you are replacing. |
| **Page eighths** | ✓ Correct, one trap | A page is treated as 8 inches; 1 inch = 1/8, and the **1st AD** measures it for the stripboard (~1 page ≈ 1 minute of screen time). `report_instruction()` already renders `2 4/8`. **The trap: 8/8 is always written "1 page", never "8/8"** — add that one line to the DPR rules or the report agent will eventually print `3 8/8` on camera. |
| **Lined script** | — Absent, and worth naming | Vertical lines drawn down the page, one per setup, marking where each angle covers the dialogue; **straight line = the actor's face is visible in that angle, squiggle = it is not.** You are effectively reconstructing this from `take_event` coverage. Saying "the lined script, rebuilt from what the camera actually saw" is a very strong, very cheap line for the VO. |
| **Setups = uniqExact(scene, shot)** | ✓ Correct | And correctly noted that a 2-camera setup is 2 take rows, 1 setup. Keep this in the VO; it is the kind of detail that separates you from a demo written by someone who has never been on a set. |
| **Camera / sound reports** | — Absent | You have `roll`, `sound_roll`, `lens_mm`, `fps`, `iso`, `tc_in`. That is 80% of a camera report. **Emitting a camera report and a sound report per roll is a near-free extra document** and completes the paperwork story. Post-hackathon, but mention it in "What's next". |
| **Statuses circled / ng / hold / wild** | ✓ Correct | `wild` for sound-only, `hold` for usable-but-not-printed — both right. |
| **DPR authorship** | ✓ Correct | `report_agent` is instructed as "the production office" (2nd AD / UPM), not the 1st AD. Correct, and worth keeping straight in the pitch. |

---

## (c) Rewritten pitch

`docs/DEVPOST.md` and `docs/DEMO_SCRIPT.md` were rewritten in this pass. The changes in substance:

- **Opens on the 1 a.m. scene and a number**, not on the architecture.
- **Every claim is now a real figure from the live database** — 2,503 takes, 26,750 events, 3,074,957 telemetry rows, 120 scenes, 66 continuity notes; day 12 = 31 setups, 175 takes, 38 circled, 42 NG, 15 min over; days 1–12 = 48 4/8 pages shot of 52 planned, 3 4/8 behind. Nothing is rounded up for effect.
- **The soft-circled-take catch is now the centrepiece** (0:38–1:05), with the 147 ms scan over 3M rows visible.
- **`mcp-clickhouse` is named on screen and in the VO**, with a full-screen hold on the trace panel — Stage 1 evidence, not a diagram.
- **Print ratio replaces shooting ratio** throughout.
- **Incumbents are named** and the boundary is drawn.
- Video retimed to **2:50** with a hard budget per beat; the 2:20–2:50 block carries the Cloud Run URL, repo URL and license on screen for the compliance sweep.

---

## (d) Stage 1 risks, and how to prove compliance

Stage 1 is pass/fail. Each of these fails the submission outright regardless of the scorecard above.

| # | Risk | State today | Proof to put in the README **and** on screen in the video |
|:--:|---|---|---|
| **R1** | **No functional hosted URL.** | 🔴 **Live blocker.** No `slateiq` Cloud Run service exists. The VM's `/health` returns `ERROR. ClickHouse connection failed.` — the MCP container cannot reach ClickHouse (read-only user credentials or the compose-internal hostname), even though ClickHouse itself answers on `/`. | Cloud Run URL in `deploy/OUTPUT.md`, in the README's first three lines, and **typed into the browser bar on camera** in the closing beat. Verify from a clean machine / incognito before submitting. |
| **R2** | **Partner not visibly used at runtime.** | 🟡 Architecturally true, publicly unproven. | Full-screen trace hold showing `run_query` + `mcp-clickhouse` + SQL + row count; a verbatim trace block in the README; `agent/evals/last_run.md` asserting *0 of 16 answers produced without a `run_query` call*; the `/api/health` MCP dot green on screen. |
| **R3** | **Gemini + Google Cloud *Agent Builder* not obviously the engine.** The rule names **Agent Builder** specifically; you say "ADK" everywhere. They are the same thing, but a compliance checker scanning for the phrase will not know that. | 🟡 True, but phrased in a way that may not match the checklist. | Write it as **"Google Cloud Agent Builder (Agent Development Kit / ADK)"** at least once in the README, once in the Devpost text and once in the VO. Show `/dev-ui/` agent tree for two seconds; keep `google-adk` visible in `agent/requirements.txt` and in the README stack table. |
| **R4** | **Video over 3:00 or not public/English.** | 🟡 Not shot. | Target **2:50** with a 10 s buffer. Unlisted-but-public YouTube, English VO, burned-in captions. Check the runtime before upload. |
| **R5** | **Repo public, licensed, runnable.** | 🟢 Public, Apache-2.0 — but **no root README**, so "run instructions" is unmet. | Root README with the 60-second quickstart, `.env.example`, and the *Tears of Steel* CC-BY 3.0 attribution visible in both README and the About screen. |
| **R6** | **"Only Google AI" rule.** | 🟢 Believed clean. | Run `grep -rniE 'openai|anthropic|claude|mistral|cohere|ollama' --include='*.py' --include='*.ts' --include='*.tsx' agent ingest db web/src` and paste the empty result into `docs/SUBMISSION.md`. Do it *after* the last commit, not before. |
| **R7** | **Broken links in the submission.** | 🔴 `agent/README.md` already links to a non-existent `evals/last_run.md`. | Sweep every relative link in every committed markdown file before submitting. A broken link inside your own proof artifact is the worst possible first impression on the Tech criterion. |
| **R8** | **Judge hits a cold start or an empty demo.** | 🟡 Cloud Run min-instances=0, ~3–5 s cold start; hosted DB may be unseeded. | Warm the service before judging opens. Seed the hosted ClickHouse and assert the row counts in `deploy/OUTPUT.md`. Add a one-line "if the first request is slow, that's a cold start on the free tier" note in the README — honest, and it pre-empts the complaint. |

### The 90 minutes that matter most

1. Fix the MCP→ClickHouse connection on the VM, seed it, deploy Cloud Run, record the URL. *(R1, R2)*
2. Run the evals; commit `last_run.md`. *(R2, R7)*
3. Write the root README around that URL, that trace and that eval number. *(R5, and the biggest single Design/Tech gain)*

Everything else on the list is a bonus. Those three are the submission.
