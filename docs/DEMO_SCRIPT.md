# SlateIQ — 3-minute demo video

**Shot and cut. Runtime 2:50.0** (hard ceiling 3:00). 1920×1080, 30 fps, h264+aac. English VO
(Gemini TTS, voice `Kore`), burned-in captions. Screen capture at 1× — never speed-ramp a query
result, the 65 ms is the point.

The pipeline that produced it lives in **`video/`** (`vo.json` → `tts.py` → `capture.mjs` →
`build.py` → `qc.py`); see `video/README.md` to regenerate. Master:
`data/video/slateiq_trailer.mp4` (gitignored). Upload copy: `video/slateiq_trailer_720p.mp4`.

**Rule for every beat: the words say the value, the screen shows the proof.** Nothing is claimed in
VO that is not visible on screen within two seconds.

---

| # | t | Screen | Voiceover |
|:--:|---|---|---|
| **1** | 0:00–0:19 | Black. A slate claps — hard cut on the clap. Title card: **SlateIQ**, and under it *Dailies intelligence*. Cut to a real Tears of Steel take playing, then freeze; structured data annotations bloom over the frozen frame — speaker, line, `soft_focus 0.52`, timecode. | "One a.m. On every film set in the world, three people are still awake — typing up what happened today. Which takes got circled. How many pages we made. Why we wrapped an hour late." |
| **2** | 0:19–0:32 | Split screen: left, a scanned-looking paper progress report and a spreadsheet. Right, the SlateIQ Ask screen, cursor blinking. On-screen text, one line at a time, adding up: `script supervisor ≈ 1 h` / `production office ≈ 45 min` / `assistant editor ≈ 1.5 h` → **`≈ 3 crew-hours per shooting day`** → **`≈ 90 hours per 30-day shoot`**. | "That's about three crew-hours a day. Ninety hours over a feature — and at the end of it, the knowledge is trapped in a PDF where nobody can ask it anything. So we built the other thing." |
| **3** | 0:32–0:57 | Ingest, fast and legible: a clip → Gemini's JSON response streaming (transcript, flags, emotion) → a terminal counter climbing → ClickHouse row counts settling on **2,503 takes · 26,750 events · 3,074,957 telemetry rows**. Then the telemetry graph overlaying the clip in real time. | "Gemini three point five Flash watches every take — dialogue, action, boom in shot, soft focus, a flubbed line. At the same time we measure the file itself, twenty-five times a second: focus, exposure, audio peak. Both land in ClickHouse. Three million rows, one production." |
| **4** | 0:57–1:24 | **The hero beat.** Ask screen. Type: **"Which circled takes are measurably soft?"** Trace panel streams: `editor_agent` → `run_query` → **`mcp-clickhouse`**. **Full-screen hold, 7.5 seconds**, on the trace: the SQL joining `take_analysis` to `frame_telemetry`, the row count, and the `43 rows` chip — then a terminal cutaway with the same join run bare: **0.065 sec, 3.09 million rows processed**. Cut back: answer card — **Scene 12, setup B, take 2 — CIRCLED — 13.0 s under threshold, avg focus 0.521.** Click it; the player seeks and plays the soft section. Freeze on the soft frame. | "Now ask it something nobody could ask before. The director circled scene twelve, take two. It's soft for thirteen seconds — and nobody caught it. That answer is a join between what Gemini *saw* and what the camera actually *measured*, across three million rows, in sixty-five milliseconds. That's a reshoot you don't have to schedule." |
| **5** | 1:24–1:44 | Two questions back to back, trace panel visible throughout. **"Where does Celia mention her robot hand?"** → scene 12 setup A, both takes, the line at 5.3 s, one CIRCLED and one NG; click, the player snaps to 5.3 s and plays. *(Shot with this question rather than "forty years" — the forty-years takes are synthetic scenes whose clips were never published, so the player would have rendered "media not published" on camera.)* Then **"Are we on schedule after day 12?"** → **48 4/8 pages shot of 52 planned — 3 4/8 behind**, the days 8 and 11 rain note called out, cumulative pages chart. | "Ask like an assistant editor — the line, the take, the timecode, and it plays from there. Ask like a producer — forty-eight and a half pages of fifty-two. Three and a half pages behind, about half a day. It knows days eight and eleven lost setups to rain, because it read the call sheets." |
| **6** | 1:44–1:53 | Continuity: **"Continuity issues in scene 41"** → `continuity_agent`, notes ranked by severity, two takes side by side with the mismatch circled. | "Ask like a script supervisor. It reads across every take of a scene and tells you which one is the odd one out — and whether you cut around it or shoot the pick-up." |
| **7** | 1:53–2:14 | **"Write today's Daily Progress Report."** `report_agent`, four `run_query` calls visible in the trace, then the markdown renders in industry format: header, per-scene table, **9 3/8 pages, 31 setups, 175 takes, 38 circled, 42 NG, wrapped 15 minutes over.** Click **Read it aloud** — Gemini TTS plays under the VO for two seconds, then ducks. | "And at wrap it writes the paperwork. The progress report, the editor's log — the facing pages, in digital form. Pages in eighths, setups, circled, N-G, overtime. Every field is a live query, not a template. And it'll read you the ninety-word version on the drive home." |
| **8** | 2:14–2:26 | Production Health **on the hosted Cloud Run service** (Grafana is wired up there via `/api/config`): *Schedule position* — **−3.50 pages / 48.50 shot / 12 days** — pages planned vs shot, print ratio by scene, scenes at risk, each panel labelled *Grafana · ClickHouse*. Then the Takes browser and a take drawer: poster frames, flag timeline, Gemini summary, transcript. | "Same database, straight through Grafana. Print ratio by scene, pages against plan, where the flags are landing. And every take in the shoot, browsable, with the problem marked on the timeline." |
| **9** | 2:26–2:42 | Architecture card animating along the path: **Gemini → Google Cloud Agent Builder (ADK) → mcp-clickhouse → ClickHouse**, with Cloud Run / Cloud Storage / Compute Engine underneath. Then a hard cut to the **hosted Cloud Run service's own About page**, punched in on the *Live* table — app URL, Grafana URL, `mcp-clickhouse health`, source, `Apache-2.0, public` — held **5.6 s**. On-screen text: `Apache-2.0` · `github.com/kaitorecca/slateiq` · `ClickHouse track`. | "Gemini and Google Cloud Agent Builder on Cloud Run. ClickHouse as the production's memory — reached only through its official M-C-P server, every query visible, every time. It's live, it's open source, and the link is right there." |
| **10** | 2:42–2:50 | Back to the slate. It claps shut on the last word. Title: **SlateIQ — your dailies, talking back.** URL held on screen. | "SlateIQ. Your dailies, finally talking back." |

---

## Shot notes

- **Beat 4 is the film.** If a beat has to be cut for time, cut 6 or 8 — never shorten the full-screen
  trace hold. "Partner used at runtime" is a pass/fail requirement and this is the evidence frame.
- The trace panel must be **visible in beats 4, 5, 6 and 7** — four separate, unedited demonstrations
  that the ClickHouse MCP server is doing the work.
- **Say "M-C-P" as letters** in the VO; TTS will otherwise try to pronounce it.
- Warm the Cloud Run service before recording beat 9. Cold start on min-instances 0 is 3–5 s and it
  will read as a broken link on camera.
- Every number spoken is a real query result. If the dataset is reseeded, re-run them and re-cut the
  VO — do not let a stale figure survive into the edit.
- **Never render `8/8`** on the DPR — that is written "1 page".
- Captions burned in, not a sidecar track, in case the judge's player doesn't load them.

## Pre-upload checklist

☑ Runtime **2:50.0** ≤ 3:00 · ☐ Public/unlisted on YouTube *(upload `video/slateiq_trailer_720p.mp4`)* ·
☑ English VO + burned captions · ☑ `mcp-clickhouse` legible on screen — full-frame for **7.5 s** in
beat 4, and in the trace panel through beats 4–7 · ☑ "Gemini" and "Google Cloud Agent Builder" both
spoken (beat 9) · ☑ hosted URL legible — **5.6 s** on the live About page + **7.9 s** on the end card ·
☑ repo URL and Apache-2.0 on screen (end card) · ☑ Tears of Steel / Blender Foundation CC BY 3.0
credit on the end card.

**Description to paste on YouTube / Devpost**

> SlateIQ turns a day of raw dailies into a queryable production brain. Gemini 3.5 Flash watches every
> take and writes structured, timestamped knowledge into ClickHouse; a Google Cloud Agent Builder (ADK)
> agent network answers editors', script supervisors', 1st ADs' and producers' questions — every
> analytical answer is SQL the agent wrote and ran through the **official `mcp-clickhouse` MCP server**,
> live, visible in the trace panel.
>
> Live: https://slateiq-957930801789.us-central1.run.app · Source (Apache-2.0):
> https://github.com/kaitorecca/slateiq · ClickHouse track.
> Footage: *Tears of Steel* © Blender Foundation, CC BY 3.0 — mango.blender.org.
