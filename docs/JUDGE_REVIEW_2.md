# Judge Review #2 — SlateIQ, **hosted only**

*Written as a Devpost judge who never clones the repo. Everything below was measured against the
**public** artifacts on 5 Sep 2026, 06:00–06:20 UTC, from a browser at 1440×900 and 390×844 driven
through Chrome DevTools, plus `curl` / `gh api`. No code was modified in this pass.*

**What a remote judge can touch:**

| Artifact | URL | Reachable |
|---|---|:--:|
| App (Cloud Run) | https://slateiq-957930801789.us-central1.run.app | ✅ 200 |
| Grafana dashboard | https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health | ✅ 200, anonymous |
| MCP health | https://35.239.36.85.sslip.io/health | ✅ `OK`, valid Let's Encrypt cert to 4 Dec 2026 |
| MCP endpoint | https://35.239.36.85.sslip.io/mcp | ✅ 401 without bearer (correct) |
| Repo | https://github.com/kaitorecca/slateiq | ✅ public, Apache-2.0, description set |

---

## (a) Scorecard — the hosted experience

| Criterion | Score | Verdict |
|---|:--:|---|
| **Technological Implementation** | **5 / 5** | This is now provable, not asserted. `/api/health` returns `mcp:"up"` and `clickhouse:"up"`; the header carries two green dots; every answer streams a live trace showing `run_query` · **`via mcp-clickhouse`** · the generated SQL · real row counts (`3 rows × 10 cols (take_id, shot, …)`) · the `LIMIT 100` the guardrail appended. Four questions, four correct answers, all numbers checked against ClickHouse: scene 27 in **20 s / 3 queries / 32 rows**; "are we on schedule after day 12" in **28 s / 2 queries** (was 124 s / 19 queries locally — a big win); 18 boom/soft-focus takes, exactly matching `uniqExact`; `drop table take` refused in **2.4 s with 0 queries**. Coordinator → specialist routing is visible and correct every time. 3.07 M telemetry rows are live on the hosted box. Nothing here is a mock. |
| **Design** | **3 / 5** | The reasoning half of the product is beautiful and the fourth screen (About) is the best compliance page I have seen in a hackathon. **But the media half of the hosted product is dead.** Every thumbnail in the Takes gallery is a striped placeholder, and clicking any take gives **"Clip unavailable — the clip could not be loaded."** The Production Health screen shows the *developer fallback text*: "Set `VITE_GRAFANA_URL` to embed the Grafana dashboard instead" — so the eight working Grafana panels never appear in the product. And the first DPR takes **~3½ minutes** with no cached result. A judge who opens Takes second (which they will — it is the second nav item) sees a product with no pictures in it. That is the difference between 3 and 5, and every cause is a build/packaging line, not a code defect. |
| **Potential Impact** | **4 / 5** | The README now leads with a person, a time and arithmetic — *≈3 crew-hours/day → ≈90 hours → two crew-weeks over a 30-day feature* — and names Frame.io C2C, Moxion, Strada, ScriptE and Filmustage accurately with the boundary drawn. The hosted answers back it up: the schedule answer reconstructs the entire 3 4/8-page deficit from the two rain days and forecasts 16.5 days needed against 18 remaining. Held off 5 only because the hosted product cannot yet *show* the join it sells — the soft-circled-take catch is not reachable from any button. |
| **Quality of the Idea** | **4 / 5** | Genuinely non-obvious and earned: a shoot as an event/time-series problem, Gemini writing rows ClickHouse later answers from. The hosted DPR proves the closed loop end to end — 175 takes, 31 setups, `Print ratio: 4.6:1 · Shooting ratio: 4.4:1` correctly distinguished, eighths rendered right. Still shy of 5 because the surface still reads "chat with your database" on arrival; the hero catch (`TOS-D12-S12-B-02-B` circled but soft for 13 s) is in the README, not on the screen. |

**Composite: 16/20** on the hosted experience. **Two hours of packaging work takes Design from 3 to 5
and the composite to 18/20** — none of it requires touching application logic.

---

## (b) Issues, prioritised

Every P0/P1 below has the same single root cause, which is worth stating once:

> **`.gcloudignore` excludes `data/thumbs/`, `data/clips/` and `data/cache/` from the Cloud Build
> upload, and `agent/Dockerfile` never `COPY`s `data/`. Separately, `GRAFANA_URL` and
> `CLIPS_BASE_URL` are set as *server* env vars on Cloud Run, but `web/` is a static Vite build —
> `import.meta.env.VITE_*` is frozen at build time, so those values never reach the browser.**

| # | Sev | Area | Repro | Expected | Actual | Suggested fix | Owner |
|:--:|:--:|---|---|---|---|---|---|
| 1 | **P0** | Media / Takes | Hosted → **Takes** → click any card | The clip plays and seeks to the flagged frame | **"Clip unavailable — The clip could not be loaded."** The player requests `https://slateiq-…run.app/clips/TOS-D12-S102-A-01-A.mp4` → **404** (`application/json`). The same file is **200 `video/mp4`** on GCS with `access-control-allow-origin: *`. No `<video>` element is even rendered. | Make the media base URL reach the client. Cheapest: `/api/health` (or `/api/takes`) already knows `CLIPS_BASE_URL` — return it and have the UI prefix relative `clip_uri`/`thumb_uri`. Alternative: rebuild `web/` with `VITE_PUBLIC_MEDIA_BUCKETS` / a media-base var set to `https://storage.googleapis.com/slateiq-media-gke-hackathon-472816` and redeploy. | `agent/` + `web/` + `deploy/` |
| 2 | **P0** | Media / thumbnails | Hosted → **Takes**, or any take card in an Ask answer | Gemini poster frames | **Every thumbnail is the striped placeholder.** `GET /thumbs/<id>.jpg` returns **HTTP 200 `text/html`, 818 bytes** — the SPA index.html catch-all — because `data/thumbs/` is in `.gcloudignore` and never lands in the image. Chrome reports it as a load, so there is no console error to notice; it just looks empty. | `data/thumbs` is **376 KB**. Either drop it from `.gcloudignore` and `COPY data/thumbs /app/data/thumbs` in `agent/Dockerfile`, or point thumbs at GCS as in #1 (GCS has all 24, 200 `image/jpeg`). Also make `/thumbs/*` and `/clips/*` return a real **404** rather than falling into the SPA fallback. | `deploy/` + `agent/` |
| 3 | **P0** | README front door | Open https://github.com/kaitorecca/slateiq | The hosted URL in the first screenful | The **Live** table reads `<<PENDING: see deploy/OUTPUT.md>>` **four times** — app, video, Grafana, MCP — and the reproduce-it curl says `<HOSTED_URL>`. The URLs have existed for over an hour. This is the single worst thing on the page: a judge's first 30 seconds end at a placeholder. | Paste the four URLs from `deploy/OUTPUT.md` into the Live table and into the curl. Also set the repo **homepage** field (currently null) to the Cloud Run URL so it shows in the GitHub About sidebar. | `docs`/root |
| 4 | **P1** | Production Health | Hosted → **Production Health** | Embedded Grafana panels | Screen renders the developer fallback: *"In-app charts derived from the take index. **Set `VITE_GRAFANA_URL` to embed the Grafana dashboard instead.**"* The Grafana dashboard is live, anonymous, embeddable and all 8 panels have data — but no judge sees it inside the product, and the sentence advertises a missing config. | Three fixes needed together: (a) build `web/` with `VITE_GRAFANA_URL=https://slateiq-grafana-hbissixc2q-uc.a.run.app`; (b) `web/src/screens/Health.tsx:21` reads `import.meta.env` directly and so bypasses the correct default already sitting in `web/src/config.ts:23` — use `config.ts`; (c) **`GRAFANA_DASH` defaults to `slateiq/production-health` but the real UID is `slateiq-prod-health`**, so the `d-solo` URL would 404 even once enabled. Verified: cross-origin `d-solo` iframe **loads fine** (`GF_SECURITY_ALLOW_EMBEDDING=true`, no `X-Frame-Options`, no CSP refusal). | `web/` + `deploy/` |
| 5 | **P1** | Grafana panel IDs | Compare `VITE_GRAFANA_PANELS` default to the live dashboard | Titles match | Default is `1:Print ratio by scene, 2:Pages vs plan, 3:Flag rate, 4:Camera hours`. Live dashboard is `1:Pages planned vs shot`, `2:Schedule position`, `3:Print ratio`, `4:Flags by type`. Every embedded panel would be **mislabelled** — and mislabelling the print-ratio panel undoes exactly the terminology repair from review #1. | Set the default from the live dashboard JSON. Best four for the product screen: `2:Schedule position`, `1:Pages planned vs shot per day`, `3:Print ratio by scene`, `8:Scenes at risk`. | `web/` |
| 6 | **P1** | DPR latency | Hosted → Production Health → **Generate Daily Progress Report** (day 12) | ~10 ms, per QC #1's pre-warmed cache | **~200–230 s.** The pre-warmed `data/cache/reports/dpr_day12.json` is committed locally but `.gcloudignore` excludes `data/cache/`, so the image ships with an empty cache and the report agent does all 15–20 round trips live. Read-aloud likewise: **42 s** cold (works, 35.9 s of audio, plays correctly). | `data/cache/reports` is **24 KB** and `data/cache/tts` is **3.7 MB**. Ship both in the image (un-ignore + `COPY`), or run one warm-up `GET /api/report/dpr?day=12` + `/api/tts` against the hosted service after each deploy and keep the instance alive. The running "Generating… 190s" clock and the explanatory copy are good and should stay — but a judge should not need them. | `deploy/` |
| 7 | **P1** | README evals | README **Evals** section vs. the artifact it links | Same numbers | README says *"15/16 reached `run_query` · 14/16 routed · judge mean **4.07/5** · median latency 45 s"*. The committed `agent/evals/last_run.md` says **16/16 reached `run_query`, 15/16 routed, mean 4.88/5, median 39.3 s**. The README **understates its own best evidence** and contradicts the file one click away. ⚠️ Worse: the working tree right now holds a **2-question** partial run in `agent/evals/last_run.*` — if that gets committed, the headline artifact becomes "Questions: 2". | Restore the README to the committed 16-question numbers, and make sure the 16-question `last_run.md`/`.json` is what ships. Do not commit a partial eval run. | root README + `agent/` |
| 8 | **P2** | Cold start | Unknown | Stated 3–5 s | Not observed cold in this pass — every measurement was warm (`/api/health` TTFB **0.73 s**, SSE first byte **0.73 s**). Revision is `maxScale=2`, no `minScale`, `startup-cpu-boost=true`, image 565 MB with a heavy ADK import. The README's "3–5 seconds" is a guess. | Measure once from a genuinely idle instance before submitting and put the real number in the README, or ping `/api/health` every 5 minutes during the judging window. | `deploy/` |
| 9 | **P2** | DPR arithmetic | Read the generated day-12 DPR totals | Consistent | `Cumulative: pages shot 48 1/2 of **115 3/8** — behind by 3 1/2 pages` mixes two denominators: 48.5 is measured against 52 planned-to-date, not against the 115 3/8 total script. As printed it does not add up. Also `48 1/2` should be `48 4/8` under the project's own eighths rule. | One line in `report_instruction()`: cumulative compares shot-to-date against **planned-to-date**; render all page figures in eighths. | `agent/` |
| 10 | **P2** | Schedule answer framing | Ask "Are we on schedule after day 12?" | One story | Opens **"Yes, we are on schedule…"**, then reports **3 4/8 pages behind**. Both are true (behind on pages, ahead on calendar) but the lead sentence inverts the demo's own narrative and reads as a contradiction on first pass. | Prompt nudge: lead with the deficit, then the forecast — *"3 4/8 pages behind, but at current pace that is 1½ days of cushion."* | `agent/` |
| 11 | **P2** | Grafana panel 3 | Open the dashboard | Readable bars | *Print ratio by scene* renders ~20 scenes as one solid green mass with overlapping labels. It is the least legible thing on an otherwise excellent dashboard. | `LIMIT 10` (or top-10 by ratio) in that panel's SQL. | `deploy/grafana` |
| 12 | **P2** | Grafana panel 8 | *Scenes at risk* table | Page eighths | `pages` column prints `0.500`, `0.620`, `0.250`. The whole project's credibility rests on eighths; this is the one place decimals leak out. | Format as eighths, or label the column `pages (decimal)`. | `deploy/grafana` |
| 13 | **P2** | Answer footer | Ask `drop table take` | Honest footer | Footer reads `0 queries · 0 rows · 2.4 s · **through mcp-clickhouse**` — nothing went through MCP. | Hide the "through mcp-clickhouse" chip when the query count is 0. | `web/` |
| 14 | **P2** | Trace attribution | Ask a second question in the same session | Hand-off shown from the coordinator | The hand-off row is labelled with the *previously active* specialist (e.g. "Editor Agent → production_agent"). Accurate ADK behaviour, but on follow-ups the coordinator appears to vanish from the trace. | Label peer transfers as `hand-off` without an originating-agent chip, or always show the coordinator row. | `web/` |
| 15 | **P2** | About page claim | About → Stack | Matches reality | *"Cloud Run + GCS — clips served from GCS"* and the diagram's *"GCS bucket · clips + thumbnails"*. True of the bucket, **false of the running product** (issues #1/#2). A judge who just hit "Clip unavailable" reads this as a claim that doesn't hold. | Resolved automatically by fixing #1/#2. | `web/` |
| 16 | **P2** | README images | Read the README | `docs/img/about.png` and `dpr.png` are the two best shots and are not used | Only 4 of 6 screenshots appear. | Add the DPR shot next to "Documents come out" — it is the most persuasive image in the set. | root README |

### Verified clean

- **0 console errors and 0 failed network requests** across Ask, Takes, Production Health and About
  (the one preserved 404 is the `/clips/*.mp4` from issue #1).
- **No mixed content, no CSP or iframe refusals.** Everything is HTTPS end to end; the cross-origin
  Grafana `d-solo` iframe loads without complaint.
- **Mobile 390×844: clean pass.** All four screens render, `scrollWidth == 390` on every one — zero
  horizontal overflow.
- **Grafana: all 8 panels return data anonymously, zero "No data"** — verified twice, once by
  replaying every panel's SQL through `/api/ds/query` unauthenticated, once by eye in the browser.
  `-3.50 pages ahead/behind`, `48.50 pages shot`, `12 days shot` are all correct.
- **README links: all 29 relative links resolve**, all 6 `docs/img/*.png` are committed and served by
  `raw.githubusercontent.com`, and the ```mermaid fence is recognised by GitHub's renderer
  (`highlight-source-mermaid`) — eyeball the rendered diagram once, since a parse error is silent.
- **Only-Google-AI grep is clean**: two hits across `agent ingest db web/src`, both comments in
  `ingest/*.py` pointing at `CLAUDE.md`. No non-Google model SDK anywhere.
- **Answer quality remains the strongest thing in this product.** Four hosted questions, zero
  hallucinated numbers, adversarial input refused in character in 2.4 s without reaching a tool.

---

## (c) The five things to do with the remaining hours

Ranked by score gained per minute. The first three are **one deploy** between them.

1. **Un-ignore and ship the small data (`data/thumbs` 376 KB, `data/cache/reports` 24 KB,
   `data/cache/tts` 3.7 MB), and make media URLs absolute to GCS.** *(~45 min · fixes P0 #1, #2, P1 #6)*
   Removes "Clip unavailable", fills the gallery with poster frames, and turns the DPR from 3½
   minutes into 10 ms. This is the whole Design gap in one change.
2. **Rebuild `web/` with `VITE_GRAFANA_URL`, fix the dashboard UID (`slateiq-prod-health`) and the
   four panel IDs, and redeploy.** *(~30 min · fixes P1 #4, #5)* Turns a line of developer
   instructions into eight live Grafana panels inside the product. The dashboard is already perfect;
   it is simply not wired in.
3. **Paste the four live URLs into the README's Live table and the curl, and set the repo homepage.**
   *(~10 min · fixes P0 #3)* Highest ratio on the list. Four placeholders are the first thing a judge
   reads and they say "unfinished".
4. **Restore the 16-question eval numbers in the README and make sure the 16-question `last_run.md`
   is what gets committed.** *(~10 min · fixes P1 #7)* You are currently advertising 4.07/5 when your
   own committed artifact says 4.88/5 — and a 2-question run is sitting uncommitted in the tree.
5. **Put the hero query on screen.** *(~30 min)* Add *"Which circled takes are measurably soft?"* as a
   fifth suggested prompt on the Ask screen. It is the one question no competitor can answer, it
   returns `TOS-D12-S12-B-02-B` — circled, 13 seconds under the focus threshold — and right now it is
   reachable only by a judge who reads to the middle of the README. That single button is the
   difference between "chat with your database" and "nobody else can do this".

*After 1–4, re-run the four prompts and the Takes/Health screens once against the redeployed service
before submitting. Then leave a browser tab polling `/api/health` so nobody lands on a cold start.*
