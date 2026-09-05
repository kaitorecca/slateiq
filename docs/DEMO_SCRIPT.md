# SlateIQ — 3-minute demo video

**Shot, cut, re-cut, committed. This is the v2 edit: runtime 2:56.1** (hard ceiling 3:00),
1920×1080 master + a 720p upload copy, 30 fps, h264+aac. English VO (Gemini TTS, voice `Kore`),
captions burned into the picture *and* shipped as `video/CAPTIONS.srt`. Screen capture at 1× —
never speed-ramp a query result, the 65 ms is the point.

**What changed from v1** (all three defects [`JUDGE_REVIEW_3.md`](JUDGE_REVIEW_3.md) found in the
trailer, closed):

1. **A 6-second cold open** in front of everything — three frozen frames pulled out of the real
   captured footage (the `clickhouse-client` benchmark, the full-frame `mcp-clickhouse` trace, the
   soft take punched in), under two caption cards. v1 spent its first thirty seconds on a cost
   argument and did not show the product until 0:35; v2 states the whole thesis before anyone
   speaks. Cost: +6 s, 2:50.0 → 2:56.1.
2. **Beat 5's producer line is now truthful.** v1's VO said "three and a half pages behind" while
   the screen's bold lead said *we are not over schedule* — the one place the narrator and the
   product visibly disagreed. `b05` was re-recorded alone: *"forty-eight and four-eighths pages of
   fifty-two — three and a half pages behind after day twelve, yet on pace to finish with a day
   and a half of cushion."* Deficit **and** forecast, which is what the product actually says.
3. **The terminal card carries a benchmark subtitle** — *"Benchmark · the agent runs this identical
   SQL through the official `mcp-clickhouse` server"* — so the bare `clickhouse-client` cutaway can
   never read as *the agent bypassed MCP for the fast number*.

Timings below are read off **`video/CAPTIONS.srt`**, the shipped cue sheet.

The pipeline that produced it lives in **`video/`** (`vo.json` → `tts.py` → `capture.mjs` →
`build.py` → `qc.py`); see `video/README.md` to regenerate. Master:
`data/video/slateiq_trailer.mp4` (gitignored). Upload copy — **the file to put on YouTube** —
`video/slateiq_trailer_720p.mp4`, committed. QC: `video/qc.py` **7/7 PASS**.

**Rule for every beat: the words say the value, the screen shows the proof.** Nothing is claimed in
VO that is not visible on screen within two seconds.

---

| # | t | Screen | Voiceover / captions |
|:--:|---|---|---|
| **0** | 0:00–0:05.4 | **Cold open — new in v2. No narration; two caption cards carry it.** Three frozen frames lifted straight out of the captured footage, 1.8 s each, cut hard: (1) the `clickhouse-client` terminal on the hero join — `0.065 sec · 3.09 million rows`, under the *Benchmark · the agent runs this identical SQL through the official `mcp-clickhouse` server* subtitle; (2) the full-frame agent trace — `run_query · via mcp-clickhouse` with the SQL legible; (3) the soft take itself, punched in (crop 1000×562) on the answer card — **`TOS-D12-S12-B-02-B` · CIRCLED · 13.0 s soft · avg focus 0.521**. | *(captions only)* **"A circled take with 13 seconds of soft focus."** → **"Found in 65 milliseconds."** |
| **—** | 0:05.4–0:07.7 | The slate claps — hard cut on the clap. Title card: **SlateIQ**, and under it *Dailies intelligence*. | *(silence — 1.7 s of lead before the first line)* |
| **1** | 0:07.7–0:23.5 | A real Tears of Steel take playing, then freeze; structured data annotations bloom over the frozen frame — speaker, line, `soft_focus 0.52`, timecode. | "One a.m. On every film set in the world, three people are still awake, typing up what happened today. Which takes got circled. How many pages we made." |
| **2** | 0:23.5–0:36.8 | The cost card: on-screen text, one line at a time, adding up — `script supervisor ≈ 1 h` / `production office ≈ 45 min` / `assistant editor ≈ 1.5 h` → **`≈ 3 crew-hours per shooting day`** → **`≈ 90 hours per 30-day shoot`**. | "That's three crew-hours a day. Ninety hours over a feature. And the knowledge ends up trapped in a PDF that can't answer a single question. So we built the other thing." |
| **3** | 0:36.8–1:01.1 | Ingest, fast and legible: a clip → Gemini's JSON response streaming (transcript, flags, emotion) → a terminal counter climbing → ClickHouse row counts settling on **2,503 takes · 26,750 events · 3,074,957 telemetry rows**. Then the telemetry graph overlaying the clip in real time. | "Gemini three point five Flash watches every take. Dialogue, boom in shot, soft focus, a flubbed line. And we measure the file itself twenty-five times a second: focus, exposure, audio peak. Both land in ClickHouse. Three million rows, one production." |
| **4** | 1:01.1–1:28.9 | **The hero beat.** Ask screen. Type: **"Which circled takes are measurably soft?"** Trace panel streams: `editor_agent` → `run_query` → **`mcp-clickhouse`**. **Full-screen hold, 7.5 s**, on the trace: the SQL joining `take_analysis` to `frame_telemetry`, the row count, the `43 rows` chip — then the terminal cutaway with the same join run bare: **0.065 sec, 3.09 million rows processed**, now under the **Benchmark** subtitle naming `mcp-clickhouse` as the agent's path (v2). Cut back: answer card — **Scene 12, setup B, take 2 — CIRCLED — 13.0 s under threshold, avg focus 0.521.** Click it; the player seeks and plays the soft section. Freeze on the soft frame. | "Now ask something nobody could ask before. The director circled scene twelve, take two. It is soft for thirteen seconds, and nobody caught it. That answer joins what Gemini saw to what the camera actually measured. Three million rows, sixty-five milliseconds, every query through the official ClickHouse M-C-P server. That's a reshoot you don't have to schedule." |
| **5** | 1:28.9–1:51.2 | Two questions back to back, trace panel visible throughout. **"Where does Celia mention her robot hand?"** → scene 12 setup A, both takes, the line at 5.3 s, one CIRCLED and one NG; click, the player snaps to 5.3 s and plays. *(Shot with this question rather than "forty years" — those takes are synthetic scenes whose clips were never published, so the player would have rendered "media not published" on camera.)* Then **"Are we on schedule after day 12?"** → **48 4/8 pages shot of 52 planned — 3 4/8 behind**, days 8 and 11 rain note, cumulative pages chart, and the forecast line the VO now matches. | **v2 — `b05` re-recorded.** "Ask like an assistant editor: the line, the take, the timecode, and it plays from there. Ask like a producer: forty-eight and four-eighths pages of fifty-two — three and a half pages behind after day twelve, yet on pace to finish with a day and a half of cushion. It knows days eight and eleven lost setups to rain." |
| **6** | 1:51.2–2:00.0 | Continuity: **"Continuity issues in scene 41"** → `continuity_agent`, notes ranked by severity, two takes side by side with the mismatch circled. | "Ask like a script supervisor. It reads across every take of a scene and tells you which one is the odd one out." |
| **7** | 2:00.0–2:21.3 | **"Write today's Daily Progress Report."** `report_agent`, four `run_query` calls visible in the trace, then the markdown renders in industry format: header, per-scene table, **9 3/8 pages, 31 setups, 175 takes, 38 circled, 42 NG, wrapped 15 minutes over.** Click **Read it aloud** — Gemini TTS plays under the VO for two seconds, then ducks. | "And at wrap it writes the paperwork. The progress report, the editor's log, the facing pages in digital form. Pages in eighths, setups, circled, N-G, overtime. Every field is a live query, not a template. And it reads you the short version out loud." |
| **8** | 2:21.3–2:33.1 | Production Health **on the hosted Cloud Run service** (Grafana is wired up there via `/api/config`): *Schedule position* — **−3.50 pages / 48.50 shot / 12 days** — pages planned vs shot, print ratio by scene, scenes at risk, each panel labelled *Grafana · ClickHouse*. Then the Takes browser and a take drawer: poster frames, flag timeline, Gemini summary, transcript. | "Same database, straight through Grafana. Print ratio by scene, pages against plan, where the flags are landing. And every take in the shoot, browsable." |
| **9** | 2:33.1–2:48.8 | Architecture card animating along the path: **Gemini → Google Cloud Agent Builder (ADK) → mcp-clickhouse → ClickHouse**, with Cloud Run / Cloud Storage / Compute Engine underneath. Then a hard cut to the **hosted Cloud Run service's own About page**, punched in on the *Live* table — app URL, Grafana URL, `mcp-clickhouse health`, source, `Apache-2.0, public` — held **5.6 s**. On-screen text: `Apache-2.0` · `github.com/kaitorecca/slateiq` · `ClickHouse track`. | "Gemini and Google Cloud Agent Builder on Cloud Run. ClickHouse as the production's memory, reached only through its official M-C-P server. It's live, it's open source, and the link is right there." |
| **10** | 2:48.8–2:56.1 | Back to the slate. It claps shut on the last word. Title: **SlateIQ — your dailies, talking back.** URL held on screen for the 3.0 s tail. | "SlateIQ. Your dailies, finally talking back." |

Cut geometry, for anyone re-timing it: `COLD = 1.80` s per cold-open still (×3), `LEAD = 1.70` s of
title before the first word, `GAP = 0.30` s of breath between beats, `TAIL = 3.00` s on the end
card, `VO_TEMPO = 1.06`. All five live in `video/build.py`; the edit is pinned to VO length, not to
footage length, so re-recording one beat never re-times the others.

---

## Shot notes

- **Beat 4 is the film, and the cold open is its trailer.** If a beat has to be cut for time, cut 6
  or 8 — never shorten the full-screen trace hold, and never drop the cold open. "Partner used at
  runtime" is a pass/fail requirement and those are the evidence frames.
- **The cold open is frozen frames, not motion**, on purpose: three real captured frames held 1.8 s
  each stay readable, where 1.8 s of moving screen capture would not. `Clip(freeze=True)` in
  `build.py` pulls the still with `ffmpeg -ss … -frames:v 1` and loops it.
- The trace panel must be **visible in beats 4, 5, 6 and 7** — four separate, unedited demonstrations
  that the ClickHouse MCP server is doing the work.
- **Say "M-C-P" as letters** in the VO; TTS will otherwise try to pronounce it.
- Warm the Cloud Run service before recording beats 8 and 9 — they are shot against the hosted
  service on purpose (Grafana is only wired up there, via `/api/config`). Cold start on
  `min-instances 0` is **~16 s** and will read as a broken link on camera; the `d-solo` iframes
  never reach `networkidle` and take ~20 s to paint.
- Every number spoken is a real query result. If the dataset is reseeded, re-run them and re-cut the
  VO — do not let a stale figure survive into the edit.
- **The VO must never contradict the bold lead on screen.** That was v1's one real defect (beat 5:
  narrator said "behind", product's headline said "not over schedule"). When the product's phrasing
  changes, the beat that narrates it is re-recorded, not left to age.
- **A bare `clickhouse-client` cutaway needs a caption saying the agent's path is MCP.** Without the
  Benchmark subtitle, the fastest number in the film appears to come from outside the partner
  integration — the opposite of what the frame is there to prove.
- **Never render `8/8`** on the DPR — that is written "1 page".
- Captions burned in, not a sidecar track, in case the judge's player doesn't load them.

## Pre-upload checklist

☑ Runtime **2:56.1** ≤ 3:00 · ☑ `video/qc.py` **7/7 PASS** · ☑ rendered and **committed** as
`video/slateiq_trailer_720p.mp4` (9.3 MB, 720p) · ☑ English VO + burned captions + sidecar
`video/CAPTIONS.srt` · ☑ `mcp-clickhouse` legible on screen — in the **cold open at 0:01.8**,
full-frame for **7.5 s** in beat 4, and in the trace panel through beats 4–7 · ☑ the bare
`clickhouse-client` benchmark is captioned as the agent's own path · ☑ VO and on-screen headline
agree on the schedule beat · ☑ "Gemini" and "Google Cloud Agent Builder" both spoken (beat 9) ·
☑ hosted URL legible — **5.6 s** on the live About page + the end-card hold · ☑ repo URL and
Apache-2.0 on screen (end card) · ☑ Tears of Steel / Blender Foundation CC BY 3.0 credit on the
end card · **☐ uploaded to YouTube, public/unlisted** — the last open box, and the only one a human
has to close. Step-by-step: **[`HANDOFF.md` §A](HANDOFF.md)**.

## Ready to paste — the YouTube listing

**Title**

```
SlateIQ — a day of dailies, turned into a database you can ask questions of
```

**Description** (chapter marks match the v2 cut above; paste the whole block)

```
SlateIQ turns a day of raw dailies into a queryable production brain.

Gemini 3.5 Flash watches every take and writes structured, timestamped knowledge into ClickHouse —
transcript, action beats, quality flags, a circle-worthy recommendation — while ffmpeg measures the
same file at 25 Hz for focus, exposure, motion and audio peak. A Google Cloud Agent Builder (ADK)
network — a coordinator plus four specialists modelled on the editor, the script supervisor, the
1st AD and the producer — then answers questions in English. Every analytical answer is SQL the
agent wrote and executed through the OFFICIAL mcp-clickhouse MCP server at runtime, visible live in
the trace panel.

The query no dailies tool can answer: "Which circled takes are measurably soft?" — a join between
Gemini's semantic judgement and 3.07 million rows of independently measured frame telemetry.
Scene 12, setup B, take 2 was circled by the director and is under the focus threshold for 13
seconds. 65 milliseconds, 3.09 million rows. Nobody on that set had noticed.

Built for Agentic Cinema: The Blockbuster Hackathon — ClickHouse partner track.

00:00  A circled take, soft for 13 seconds, found in 65 ms
00:07  1 a.m. — three people still typing up the day
00:36  Gemini watches every take; ffmpeg measures every frame
01:01  The hero query — mcp-clickhouse, live, 65 ms over 3.09M rows
01:29  Ask like an assistant editor, ask like a producer
01:51  Ask like a script supervisor — continuity
02:00  It writes the Daily Progress Report, and reads it aloud
02:21  Production Health — Grafana on the same database
02:33  Gemini → Agent Builder (ADK) → mcp-clickhouse → ClickHouse
02:48  Your dailies, finally talking back

Try it (live, no login): https://slateiq-957930801789.us-central1.run.app
Source, Apache-2.0: https://github.com/kaitorecca/slateiq
Dashboard (anonymous): https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health

Built with Gemini 3.5 Flash · Google Cloud Agent Development Kit (Agent Builder) · the official
mcp-clickhouse MCP server · ClickHouse · Cloud Run · Cloud Storage · Secret Manager · Grafana.

Footage: "Tears of Steel" © Blender Foundation, mango.blender.org, licensed CC BY 3.0. SlateIQ is
not affiliated with or endorsed by the Blender Foundation. All schedule, scene and telemetry data
for the 30-day shoot is synthetic.
```

**Tags**

```
gemini, google adk, agent development kit, agent builder, vertex ai, clickhouse, mcp, model context protocol, mcp-clickhouse, cloud run, grafana, film production, dailies, script supervisor, hackathon, ai agents, google cloud
```

**Short version**, for the Devpost video field or anywhere with a character limit:

> SlateIQ turns a day of raw dailies into a queryable production brain. Gemini 3.5 Flash watches
> every take and writes structured, timestamped knowledge into ClickHouse; a Google Cloud Agent
> Builder (ADK) agent network answers the editor's, script supervisor's, 1st AD's and producer's
> questions — every analytical answer is SQL the agent wrote and ran through the **official
> `mcp-clickhouse` MCP server**, live, visible in the trace panel.
>
> Live: https://slateiq-957930801789.us-central1.run.app · Source (Apache-2.0):
> https://github.com/kaitorecca/slateiq · ClickHouse track.
> Footage: *Tears of Steel* © Blender Foundation, CC BY 3.0 — mango.blender.org.

Upload mechanics — visibility, the `CAPTIONS.srt` subtitle track, and where the resulting URL has
to be pasted — are in **[`HANDOFF.md`](HANDOFF.md) §A–§B**.
