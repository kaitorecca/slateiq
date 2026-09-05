# Judge Review #3 — SlateIQ, the complete submission package

*Written as a Devpost judge with **ten minutes** for this entry: watch the trailer, skim the Devpost
page, open the repo, click the live link. Measured 5 Sep 2026 against the public artifacts and the
committed video. Frames extracted at 5 s intervals from `video/slateiq_trailer_720p.mp4` and looked
at; `video/CAPTIONS.srt` and `video/vo.json` read line by line; every number re-verified against
ClickHouse `localhost:8123` and `agent/evals/last_run.md`. No code and no video files were modified;
`docs/DEVPOST.md` was edited (see §e).*

Previous passes: [`JUDGE_REVIEW_1.md`](JUDGE_REVIEW_1.md) (repo-only), [`JUDGE_REVIEW_2.md`](JUDGE_REVIEW_2.md) (hosted-only).

---

## (a) Scorecard

| Criterion | #1 | #2 | **#3** | The one sentence that decides it |
|---|:--:|:--:|:--:|---|
| **Technological Implementation** | 4 | 5 | **5 / 5** | The claim and the proof are now the same artifact: the trailer holds 7.5 s on a full-frame trace panel reading `run_query` · **`via mcp-clickhouse`** · the generated SQL · `43 rows`; the hosted `/api/health` returns `mcp:"up"`, `clickhouse:"up"`, `clickhouse_mcp_auth:true`; and a live question I asked just now routed coordinator → `editor_agent` and fired **3 `run_query` calls through MCP in 31.5 s**, returning `TOS-D12-S12-B-02-B` at 13.0 s soft / avg 0.521 — the exact row I get from ClickHouse myself in **65 ms over 3.09 M rows**. `agent/evals/last_run.md` is 28 questions, 28/28 through MCP, judge mean 4.82/5, with every SQL statement committed. Nothing in this project asks to be taken on faith. |
| **Design** | 4 | 3 | **5 / 5** | Every P0 from review #2 is gone. Thumbnails load (`200 image/jpeg` from GCS), clips serve `206 video/mp4`, the Production Health screen now embeds the **real Grafana panels** with the correct UID and correctly-labelled panel titles (`/api/config` serves them at runtime instead of a frozen Vite build), and the Daily Progress Report that took 3½ minutes returns in **0.68 s**. The trailer's four-screen tour (Ask → Takes → Health → About) is a coherent cutting-room product in one visual language, and the closing card carries the live URL and the repo. |
| **Potential Impact** | 3 | 4 | **4 / 5** | The arithmetic is now stated everywhere and consistently — 1 h + 45 min + 1.5 h ≈ **3 crew-hours/day → ~90 h over a feature**, held on screen at 0:20–0:32 as a build, and the competitive boundary (Frame.io C2C, Moxion, Strada, ScriptE, Filmustage) is drawn accurately and without strawmanning. Still short of 5 because the value is always expressed as *hours saved*, never as *money or footage saved* — the soft circled take is a reshoot avoided, and nobody ever says what a reshoot day costs. One number would close this. |
| **Quality of the Idea** | 3 | 4 | **4 / 5** | "A shoot is an event-stream problem wearing a clipboard" is a genuinely non-obvious reframe, and the product earns it: the semantic layer (Gemini) and the measured layer (ffmpeg at 25 Hz) in the *same* query is a join nobody else in this space can execute. Held at 4 for one reason only, and it is a trailer problem rather than a product problem — see §b. |

**Composite: 18 / 20.** Up from 15 (repo-only) and 16 (hosted-only). The package is submission-ready
today; everything below is polish, and the top three items are worth roughly one point between them.

---

## (b) The trailer — shot by shot

`video/slateiq_trailer_720p.mp4` · **2:49.8** · 1280×720 · 30 fps · h264 + aac · 8.5 MB · burned-in
captions plus `CAPTIONS.srt`. Ten VO beats, `gemini-2.5-flash-preview-tts` voice **Kore**. Ten
0.3 s black dips between beats — deliberate, and they read as edits, not dropouts.

**Verdict: this is the strongest hackathon trailer I have seen this round.** It is a *film* about a
film problem, not a screen recording with a voice over it. The three things that matter to a judge —
what it is, that it is real, and where to click — all land. Everything below is refinement.

### Is the story clear in 30 seconds? **No — and that is the one real structural note.**

A judge with ten minutes per entry does not watch 2:50; they watch the first 20–30 s and then scrub.
At **0:30** this trailer is still on the cost-of-paperwork card. The first product frame is at
**0:35**, the first `mcp-clickhouse` evidence at **1:00**, the 65 ms hero at **1:15**. A judge who
bails at 0:30 has seen a problem statement and no product, no Gemini, no ClickHouse, no MCP.

**Fix (≈20 min, highest-value change on this list):** cut a **6-second cold open** and paste it in
front of the current 0:00 — three shots, no VO, just the existing captions or a card:
`3.07 M rows · 65 ms` (the terminal frame you already have at 1:15) → the trace panel reading
`via mcp-clickhouse` (the frame at 1:00) → the take card `12/B/2 CIRCLED · soft 13.0 s`. Then run the
existing film. The total goes to 2:56 — still inside three minutes — and the first six seconds carry
the entire technical claim.

### Shot-by-shot

| Timestamp | What is on screen | Issue | Severity | Fix |
|---|---|---|:--:|---|
| **0:00–0:03** | Slate title card, `TEARS OF STEEL · DAY 12/30 · ROLL A012` | None — an excellent, confident open that instantly says "film". Slate detail is correct. | — | Keep. |
| **0:05–0:19** | Tears of Steel footage with a burned-in slate strip; Gemini dialogue/emotion/flag chips build in | The chips are the best explanatory device in the film. Minor: at 720p the slate strip (`SC 12 · SETUP A · TAKE 1 · CAM A · 01:12:04:08`) is ~9 px tall and unreadable on a laptop; on the 1080p master it is fine. | P3 | If you re-export, bump the strip 2 pt. Otherwise ignore — YouTube will serve 1080p. |
| **0:20–0:32** | Cost card: 1 h / 45 min / 1.5 h → **≈3 crew-hours** → **≈90 hours** | Numbers land, build is well-paced, typography is clean. **But this is 12 s of static text at exactly the moment a scrubbing judge decides whether to stay.** | **P1** | Covered by the cold-open fix above. Do not shorten the card itself — the arithmetic is the impact case. |
| **0:30** | (still on the cost card) | **The 30-second scrub point contains no product.** | **P1** | Cold open. |
| **0:35–0:55** | Ingest card: clip player, Gemini structured JSON, focus/exposure/audio meters, counters ticking to **2,503 / 26,750 / 3,074,957** | Verified exact against ClickHouse (`count()` = 2503 / 26750 / 3074957). Best single explanatory frame in the film — semantic and measured layers side by side. | — | Keep. Consider holding 1 s longer on the final counter values. |
| **0:53** | Caption *"…Both land in ClickHouse."* | The word **ClickHouse** is spoken and captioned but no ClickHouse mark or logo is on screen until 2:30. For a partner-track entry that is a missed beat. | P2 | Add the ClickHouse wordmark under the counter row for these 4 s. Zero re-record needed. |
| **0:55–1:00** | Ask screen, answer + take gallery, caption *"Now ask something nobody could ask before."* | Caption sits directly over the chat input box; legible, but it is the only place text lands on text. | P3 | Nudge the caption baseline up ~40 px for this beat only. |
| **1:00–1:12** | **Full-frame agent trace**: `transfer_to_agent` → `editor_agent`, `run_query` **`via mcp-clickhouse`**, full SQL, `43 rows × 10 cols` | **The single most important frame in the submission, and it is unmistakable.** Stage-1 evidence: unambiguous. Header line *"executed against ClickHouse through the official `mcp-clickhouse` server at runtime"* is exactly right. Minor: the SQL is ~11 px at 720p. | — | Keep. If anything, hold it longer. |
| **1:15–1:22** | Terminal: `clickhouse-client --time < hero.sql` → `TOS-D12-S12-B-02-B · 13.0 · 0.521`, **`0.065 sec`, `3.09 million rows`, `1.14 GB/s`** | Verified: I ran the same query three times and got **65.6 / 56.0 / 63.8 ms**. **But the VO over this shot says "every query through the official ClickHouse MCP server" while the screen shows a bare `clickhouse-client` invocation.** A ClickHouse-track judge will notice the tool mismatch. Everything is true — the *agent* path is MCP, this terminal is a benchmark — but the frame and the sentence disagree. | **P1** | No re-record needed. Add a one-line subtitle to the terminal card: `benchmark — the agent runs the identical SQL through mcp-clickhouse (see 1:00)`. Or re-order so the VO line "…through the official ClickHouse MCP server" sits over the trace frame at 1:00 and the terminal carries only "sixty-five milliseconds". |
| **1:25–1:32** | Assistant-editor question, take cards, player seeking to 5.3 s | Works, plays, timecode cited. Exactly the "it plays from there" claim. | — | Keep. |
| **1:33–1:44** | Producer question. Screen reads **"We are not over schedule. In fact, we are projected to finish with about 1 1/2 days of cushion"**; VO says **"forty-eight and a half pages of fifty-two, three and a half behind."** | **The VO and the screen say opposite things in the same three seconds.** Both are true (behind on pages, ahead on the calendar) but a judge reading the bold first line while hearing "three and a half behind" reads it as the agent contradicting the narrator. This is JR#2 issue #10, now amplified because it is on camera. | **P0 for the trailer** | Cheapest: re-record beat `b05` only (`tts.py` is cached by text hash, so one beat re-synthesises) to *"Ask like a producer: three and a half pages behind on the page count, a day and a half of cushion on the calendar."* Cheaper still and no re-record: nudge `report`/`production_instruction()` to lead with the deficit and re-shoot that one Playwright beat. Either is ~30 min. |
| **1:39** | Same shot | VO says *"forty-eight and a half pages"*; the screen and the whole project say **48 4/8**. The Devpost page itself declares eighths a credibility marker. | P2 | Same beat re-record: *"forty-eight and four-eighths of fifty-two."* Fold into the fix above. |
| **1:45–1:55** | Script-supervisor question, cross-take continuity, "the odd one out" | Strong. The severity-scored mismatches are genuinely impressive and unique. | — | Keep. |
| **2:00–2:15** | Production Health with DPR + Editor's Log; audio player runs `0:02 / 0:35` | Read-aloud proven on camera, which is the right way to prove it. Minor: VO says *"pages in eighths, setups, circled, NG, overtime"* while the visible portion of the panel is scrolled to **continuity notes**; the day-totals line with those fields is on screen only at 2:00. | P2 | Slow the auto-scroll ~30% across 2:04–2:12 so the totals line is under the VO that names it. |
| **2:17–2:26** | **Real Grafana panels**: `-3.50` pages ahead/behind, `48.50` pages shot, `12.00` days shot, print ratio by scene, scenes at risk | Verified live and anonymous; `/api/config` serves the correct UID `slateiq-prod-health` and the four correct panel titles. JR#2 issues #4 and #5 fully closed. Remaining nit: *Print ratio by scene* is still a dense green mass of ~20 bars (JR#2 #11). | P3 | Top-10 `LIMIT` on that panel. Cosmetic. |
| **2:26–2:30** | Takes browser, take detail with transcript and flag timeline | Thumbnails all present. JR#2 #1/#2 closed. | — | Keep. |
| **2:30–2:40** | Architecture card: **Gemini 3.5 Flash → Agent Builder (ADK) → `mcp-clickhouse` → ClickHouse**, Cloud Run / Cloud Storage / Compute Engine strip, headline **"One data path. No bypass."** | The best static card in the film and the clearest statement of the partner integration anywhere in the submission. Row counts on it (2,503 / 26,750 / 3,074,957) verified. | — | Keep. This is the frame to screenshot for the Devpost gallery. |
| **2:40–2:45** | README scroll showing the filled-in **Live** table (app, Grafana, MCP health, source) | Good closing evidence — it proves the links exist rather than asserting it. | — | Keep. |
| **2:45–2:50** | End card: logo, **live Cloud Run URL**, **github.com/kaitorecca/slateiq**, Apache-2.0, Tears of Steel CC BY 3.0 credit | Correct, legible, and the attribution is handled properly. The tagline shifts from *"Your dailies, finally talking back"* (VO/caption) to *"Your dailies, talking back."* (card). | P3 | Pick one. The card version is better. |
| **throughout** | Captions | 45 cues, no overlaps, no orphan lines, sensible 2–5 s durations, acronyms de-spelled correctly (VO says "M C P", caption shows **MCP**). `CAPTIONS.srt` matches the burn-in exactly. Mix is even; no clipping. | — | Nothing to do. |

### Claims audited against the product

| VO claim | Verdict |
|---|---|
| "Gemini 3.5 Flash watches every take" | ✅ `ingest/config.py:40`, `/api/health` reports `model: gemini-3.5-flash` |
| "twenty-five times a second" | ✅ 25 Hz telemetry; the card reads `25 samples/s` |
| "Three million rows, one production" | ✅ 3,074,957 |
| "sixty-five milliseconds" | ✅ measured 56–66 ms, three runs |
| "every query through the official ClickHouse MCP server" | ✅ for the agent path (`run_query` is the specialists' only tool) — **but the frame under it shows `clickhouse-client`.** See 1:15. |
| "It is soft for thirteen seconds" | ✅ 13.0 s under 0.55, avg 0.521 |
| "forty-eight and a half of fifty-two, three and a half behind" | ✅ arithmetically, **✗ against the screen's own lead sentence.** See 1:33. |
| "days eight and eleven lost setups to rain, because it read the call sheets" | ✅ reproduced live |
| "Every field is a live query, not a template" | ✅ DPR is agent-generated (pre-warmed cache, same content) |
| "Same database, straight through Grafana" | ✅ Grafana reads the same ClickHouse |
| "It's live, it's open source, and the link is right there" | ✅ URL is on the end card |
| Terminology — circled / NG / setups / print ratio vs shooting ratio / eighths | ✅ correct throughout; "print ratio" used correctly, never "shooting ratio" for takes-per-circle. The only slip is *"forty-eight and a half"* for `48 4/8`. |

---

## (c) The rest of the package

**`docs/DEVPOST.md`** — was the weakest artifact in the set and is now the most improved; see §e for
what I changed. Before the edit it carried **`147 ms`** for the hero query (real figure: **65 ms** —
the trailer, README and `TRACKING.md` had all been updated, this had not), claimed **16** eval
questions when the committed run is **28**, and shipped `HOSTED_URL` / `VIDEO_URL` placeholders in the
header *and* the footer. A judge who reads the Devpost page before the repo — which is what a judge
does — would have hit an unfilled template on the "Try it" line.

**README (GitHub)** — genuinely strong. Live table filled with four working URLs, repo homepage set,
Apache-2.0, six topics, a ten-second `curl` reproduction of the partner call, an accurate mermaid
architecture diagram, six screenshots, and eval numbers (28/28, 4.82/5, 27.3 s median) that match
`agent/evals/last_run.md` exactly — JR#2 issue #7 closed, and it now *overstates nothing*. The cold
start is measured (~16 s from Cloud Run logs) rather than guessed. Only gap: the video row still reads
*"uploading"*.

**Hosted 5-minute smoke** — all green.

| Check | Result |
|---|---|
| `/api/health` | `200` in **0.73 s** · `mcp:"up"` · `clickhouse:"up"` · `clickhouse_mcp_auth:true` |
| Chat — *"Which circled takes are measurably soft?"* | `200`, **31.5 s**, coordinator → `editor_agent`, **3 `run_query` calls**, leads with `TOS-D12-S12-B-02-B` at 13.0 s soft / 0.521 avg / 0.424 worst. Every number matches my own ClickHouse query. |
| Takes / media | `/api/takes` returns absolute GCS URLs; thumbnail `200 image/jpeg`, clip `206 video/mp4`. **JR#2 P0 #1 and #2 closed.** |
| Production Health | `/api/config` serves the correct Grafana UID and four correctly-titled panels; `d-solo` embed returns `200`. **JR#2 P1 #4 and #5 closed.** |
| DPR day 12 | **0.68 s** (was ~200 s). **JR#2 P1 #6 closed.** |

---

## (d) Final prioritised list for the last hours

Ranked by score gained per minute.

| # | Do this | Time | Why it is worth it |
|:--:|---|:--:|---|
| **1** | **Upload the video and paste the URL** into `README.md` (Live table), `docs/DEVPOST.md` (`VIDEO_URL`, two places), `docs/SUBMISSION.md`, and the Devpost form. | 15 min | The only genuine hole left in the package. Nothing else matters if the trailer is not attached. |
| **2** | **Fix the producer beat (1:33).** Re-record VO beat `b05` alone — *"three and a half pages behind on the page count, a day and a half of cushion on the calendar"* — or nudge the production agent to lead with the deficit and re-shoot that one Playwright beat. Same edit fixes *"forty-eight and a half"* → *"forty-eight and four-eighths."* | 30 min | It is the one moment where the narrator and the product visibly disagree, and a judge only needs to notice it once. |
| **3** | **Add the 6-second cold open** (65 ms terminal → `via mcp-clickhouse` trace → `12/B/2 CIRCLED · soft 13.0 s`) in front of 0:00. | 20 min | Puts the entire technical claim inside the window a ten-minute judge actually watches. Total runtime 2:56, still under three minutes. |
| **4** | **Subtitle the terminal card at 1:15**: `benchmark — the agent runs the identical SQL through mcp-clickhouse`. | 10 min | Removes the only frame where a partner-track judge could accuse the film of showing a non-MCP path under an MCP sentence. |
| **5** | **Fix the DPR cumulative line** — `48 4/8 of 115 3/8 — behind by 3 4/8` still mixes denominators (JR#2 #9, still live: I reproduced it on the hosted DPR just now). Compare shot-to-date against **planned-to-date (52)**, not the 115 3/8 total script. | 20 min | It is the one place in the product where the arithmetic visibly does not add up, in the document the whole "it writes the paperwork" claim rests on. Requires re-warming the day-12 cache. |
| **6** | **Put a cost on the reshoot.** One clause in the Devpost "What it does" §3 and in the README: *"a reshoot day on a mid-budget feature is $80–150 k."* | 10 min | The only thing standing between Potential Impact 4 and 5. Right now the pitch converts to hours, never to money. |
| **7** | Add the ClickHouse wordmark under the counter row at 0:53. | 10 min | Partner-track visibility during the exact four seconds the VO names ClickHouse. |
| **8** | Slow the DPR auto-scroll at 2:04–2:12; nudge the 0:55 caption off the input box; `LIMIT 10` on the Grafana print-ratio panel; settle on one tagline. | 20 min | Cosmetic. Do these only if 1–6 are done. |

Do **1** now. Do **2** and **3** if there are two hours left. **5** is the last substantive defect in
the product itself. Everything below **6** is polish on an already-strong package.

---

## (e) Changes made to `docs/DEVPOST.md` in this pass

Every figure below was re-verified before it was written — hero query timed three times against
`localhost:8123` (56.0 / 63.8 / 65.6 ms, 3,086,083 rows read), counts from `count()` on the live
tables, eval figures from `agent/evals/last_run.md`, schedule figures reproduced on the hosted app.

| Line | Was | Now | Why |
|---|---|---|---|
| Header | `Fill before submitting: HOSTED_URL, VIDEO_URL` | Live Cloud Run URL inline; only `VIDEO_URL` outstanding; verification date added | A judge should never see an unfilled placeholder. |
| Tagline | ended on *"in SQL you can read"* | ends on *"It caught a circled take that is soft for 13 seconds. Nobody on that set had noticed."* | The tagline described a mechanism; now it lands the catch. Also drops the awkward "Agent Builder crew". |
| §What it does 2 | *"Three and a half pages behind — about half a day."* | adds the reconstruction: 4.04 pages/day, 16.5 days needed against 18 remaining | Shows the agent reasoning rather than retrieving. Both figures reproduced live. |
| §What it does 3 | *"Scene 12, setup B, take 2 … averaging 0.52"* | full take id, the director's note, 13.0 of 16.2 s, avg 0.521, worst 0.424, "six more behind it" | The take id is checkable; "six more" shows it is a query, not a demo fixture. |
| §What it does 3 | **`147 ms`** ⚠️ **stale** | **`65 ms — 3.09 million rows scanned, 1.14 GB/s`**, plus "first suggested prompt on the Ask screen" | The 147 ms figure was wrong by 2.3×, and it was the one number a ClickHouse judge would check. |
| §How we built it | *"runs 16 real questions"* ⚠️ **stale** | **28 questions**, 28/28 through MCP, 27/28 routing, judge mean 4.82/5, median 27.3 s | Understated its own best evidence and contradicted the file it linked. |
| Footer | `Try it: HOSTED_URL … Video: VIDEO_URL` | live app URL with the hero prompt to type, Grafana dashboard link, cold-start honesty note | Tells the judge exactly what to click and what to ask, and pre-empts a cold start being read as a broken app. |

Unchanged and re-verified as correct: 2,503 takes · 26,750 events · **120 scenes** · 66 continuity
notes · 3,074,957 telemetry rows; ADK **2.8.0**; ClickHouse **25.6.13.41**; day 12 = 31 setups / 175
takes / 38 circled / 42 NG / 9 3/8 pages / 15 min over; 48 4/8 of 52 pages.
