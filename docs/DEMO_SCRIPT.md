# SlateIQ — 3-minute demo video

**Target 2:50** (hard ceiling 3:00 — leave the buffer). 1920×1080, 30 fps. English VO (Gemini TTS,
voice `Kore`), burned-in captions. Screen capture at 1× — never speed-ramp a query result, the 147 ms
is the point.

**Rule for every beat: the words say the value, the screen shows the proof.** Nothing is claimed in
VO that is not visible on screen within two seconds.

---

| # | t | Screen | Voiceover |
|:--:|---|---|---|
| **1** | 0:00–0:12 | Black. A slate claps — hard cut on the clap. Title card: **SlateIQ**, and under it *Dailies intelligence*. Cut to a real Tears of Steel take playing, then freeze; structured data annotations bloom over the frozen frame — speaker, line, `soft_focus 0.52`, timecode. | "One a.m. On every film set in the world, three people are still awake — typing up what happened today. Which takes got circled. How many pages we made. Why we wrapped an hour late." |
| **2** | 0:12–0:24 | Split screen: left, a scanned-looking paper progress report and a spreadsheet. Right, the SlateIQ Ask screen, cursor blinking. On-screen text, one line at a time, adding up: `script supervisor ≈ 1 h` / `production office ≈ 45 min` / `assistant editor ≈ 1.5 h` → **`≈ 3 crew-hours per shooting day`** → **`≈ 90 hours per 30-day shoot`**. | "That's about three crew-hours a day. Ninety hours over a feature — and at the end of it, the knowledge is trapped in a PDF where nobody can ask it anything. So we built the other thing." |
| **3** | 0:24–0:44 | Ingest, fast and legible: a clip → Gemini's JSON response streaming (transcript, flags, emotion) → a terminal counter climbing → ClickHouse row counts settling on **2,503 takes · 26,750 events · 3,074,957 telemetry rows**. Then the telemetry graph overlaying the clip in real time. | "Gemini three point five Flash watches every take — dialogue, action, boom in shot, soft focus, a flubbed line. At the same time we measure the file itself, twenty-five times a second: focus, exposure, audio peak. Both land in ClickHouse. Three million rows, one production." |
| **4** | 0:44–1:06 | **The hero beat.** Ask screen. Type: **"Which circled takes are measurably soft?"** Trace panel streams: `editor_agent` → `run_query` → **`mcp-clickhouse`**. **Full-screen hold, 4 seconds**, on the trace: the SQL joining `take_analysis` to `frame_telemetry`, the row count, `147 ms`. Cut back: answer card — **Scene 12, setup B, take 2 — CIRCLED — 13.0 s under threshold, avg focus 0.521.** Click it; the player seeks and plays the soft section. Freeze on the soft frame. | "Now ask it something nobody could ask before. The director circled scene twelve, take two. It's soft for thirteen seconds — and nobody caught it. That answer is a join between what Gemini *saw* and what the camera actually *measured*, across three million rows, in a hundred and forty-seven milliseconds. That's a reshoot you don't have to schedule." |
| **5** | 1:06–1:24 | Two questions back to back, trace panel visible throughout. **"Every take where Celia says 'forty years'"** → results with timecodes, click, player snaps to the offset. Then **"Are we on schedule after day 12?"** → **48 4/8 pages shot of 52 planned — 3 4/8 behind**, the days 8 and 11 rain note called out, cumulative pages chart. | "Ask like an assistant editor — the line, the take, the timecode, and it plays from there. Ask like a producer — forty-eight and a half pages of fifty-two. Three and a half pages behind, about half a day. It knows days eight and eleven lost setups to rain, because it read the call sheets." |
| **6** | 1:24–1:38 | Continuity: **"Continuity issues in scene 41"** → `continuity_agent`, notes ranked by severity, two takes side by side with the mismatch circled. | "Ask like a script supervisor. It reads across every take of a scene and tells you which one is the odd one out — and whether you cut around it or shoot the pick-up." |
| **7** | 1:38–2:04 | **"Write today's Daily Progress Report."** `report_agent`, four `run_query` calls visible in the trace, then the markdown renders in industry format: header, per-scene table, **9 3/8 pages, 31 setups, 175 takes, 38 circled, 42 NG, wrapped 15 minutes over.** Click **Read it aloud** — Gemini TTS plays under the VO for two seconds, then ducks. | "And at wrap it writes the paperwork. The progress report, the editor's log — the facing pages, in digital form. Pages in eighths, setups, circled, N-G, overtime. Every field is a live query, not a template. And it'll read you the ninety-word version on the drive home." |
| **8** | 2:04–2:20 | Production Health: Grafana panels over the same ClickHouse tables — print ratio by scene, pages against plan, flag rate, camera hours. Then the Takes browser scrubbing past, flag chips visible. | "Same database, straight through Grafana. Print ratio by scene, pages against plan, where the flags are landing. And every take in the shoot, browsable, with the problem marked on the timeline." |
| **9** | 2:20–2:42 | Architecture diagram animating along the path: **Gemini → Google Cloud Agent Builder (ADK) → mcp-clickhouse → ClickHouse**, on **Cloud Run** and GCS. Then a hard cut to a browser: the **Cloud Run URL typed into the address bar** and loading live, `/api/health` dots green. On-screen text: `Apache-2.0` · `github.com/kaitorecca/slateiq` · `ClickHouse track`. | "Gemini and Google Cloud Agent Builder on Cloud Run. ClickHouse as the production's memory — reached only through its official M-C-P server, every query visible, every time. It's live, it's open source, and the link is right there." |
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

☐ Runtime ≤ 3:00 · ☐ Public/unlisted on YouTube · ☐ English VO + burned captions ·
☐ `mcp-clickhouse` legible on screen at least once · ☐ "Gemini" and "Google Cloud Agent Builder"
both spoken · ☐ hosted URL legible for ≥ 3 s · ☐ repo URL and Apache-2.0 on screen ·
☐ Tears of Steel / Blender Foundation CC-BY credit in the end card or description.
