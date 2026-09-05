# HANDOFF — the last mile, by hand

Everything in SlateIQ is built, deployed, tested and committed. **Two things are left, and both
need a human being: upload the video to YouTube, and fill in the Devpost form.** This page is the
copy-paste script for doing exactly that.

**Deadline: 9 Sep 2026, 14:00 PDT = 10 Sep 2026, 07:00 AEST (Sydney).**
Judging window: **23 Sep – 7 Oct 2026** — the VM and Cloud Run must stay alive through it (§E).

---


> **Ops already in place (5 Sep):** Cloud Scheduler `slateiq-keepwarm` pings `/api/health` every 5 min (warm instance), and a Cloud Monitoring uptime check emails the owner's Gmail if the hosted health stops saying `mcp:up`. Both are free-tier; see deploy/README.md.

> **Small follow-up (P2, optional):** Cloud Run rev `slateiq-00013` predates commit `eb10466`, so the baked Editor's Log cache (`data/cache/reports/editor_log_day12.json`) is missing from the image — the first `/api/report/editor-log?day=12` on a cold instance takes ~100 s (no UI button calls it; CSV/ALE exports and the DPR are unaffected). Fix = one redeploy when gcloud is responsive: `bash deploy/cloudrun/deploy_agent.sh` (~5 min). Two attempts on 5 Sep ~21:00 hung inside gcloud (`projects describe` / `services list` never returned) and were killed.

> **⚠️ Trạng thái 5 Sep 21:35 (AEST): hạ tầng đã TẮT theo yêu cầu tiết kiệm chi phí.** VM `slateiq-data` đã stop (ClickHouse + mcp-clickhouse offline → hosted app trả `mcp:down`, Grafana không có dữ liệu); Cloud Scheduler keep-warm đã pause; uptime check/alert đã xóa. Để bật lại trước khi giám khảo chấm (23 Sep–7 Oct): `gcloud compute instances start slateiq-data --zone us-central1-a`, chờ ~2 phút, lấy IP mới (`gcloud compute instances describe slateiq-data --zone us-central1-a --format='value(networkInterfaces[0].accessConfigs[0].natIP)'`), rồi chạy lại `bash deploy/vm/deploy_stack.sh` (Caddy cert cho `<ip-mới>.sslip.io`), cập nhật `CLICKHOUSE_MCP_URL` trong `.secrets/deploy.env`, chạy `bash deploy/cloudrun/deploy_agent.sh` và `bash deploy/grafana/deploy.sh`, sau đó `bash deploy/vm/healthcheck.sh`. Dữ liệu trên đĩa VM vẫn còn (pd-standard 30GB, không cần seed lại).

## Tóm tắt tiếng Việt (đọc cái này trước)

Sản phẩm đã xong hết: code, deploy, test, video. **Chỉ còn 2 việc cần bạn tự làm bằng tay:**

1. **Upload video lên YouTube.** File là `video/slateiq_trailer_720p.mp4` (2:56, 9.3 MB, đã có
   phụ đề cháy sẵn trong hình). Tiêu đề / mô tả / tag đã viết sẵn ở **§A** bên dưới — copy paste
   nguyên si. Nhớ bật **Public** (hoặc Unlisted), chọn **"No, it's not made for kids"**, và
   upload thêm file phụ đề `video/CAPTIONS.srt` ở mục Subtitles (tiếng Anh).
2. **Dán link YouTube vào 3 chỗ + điền form Devpost.**
   - `README.md` **dòng 55** (§B1)
   - `docs/SUBMISSION.md` dòng có chữ "Video" (§B2)
   - `docs/DEVPOST.md` **dòng 3 và dòng 186** — thay chữ `VIDEO_URL` (§B3)
   - Rồi commit + push (§B4), sau đó điền form Devpost theo **§C** (từng ô một, đã soạn sẵn chữ).

**Thứ tự làm:** A → B → C → D (chạy 3 lệnh kiểm tra trước khi bấm Submit) → bấm **Submit** trên
Devpost trước **07:00 sáng 10/9 giờ Sydney**.

**Sau khi nộp:** đừng tắt VM cho tới hết ngày **7/10** (ban giám khảo chấm 23/9 – 7/10). Xem **§E**.
Chi phí duy nhất là địa chỉ IPv4 của VM, khoảng **2,5 USD/tháng** — mọi thứ khác nằm trong
Always Free tier. Nếu muốn dừng tính tiền sau ngày 7/10: `gcloud compute instances stop slateiq-data`
(**đừng xoá** — máy có deletion protection và chứa toàn bộ dataset demo).

**§F là tuỳ chọn** (submission thứ hai cho Grafana track). Không bắt buộc, chỉ làm nếu còn thời gian.

---

## A — Upload the video to YouTube

**File to upload:** `video/slateiq_trailer_720p.mp4`
(2:56.1 runtime — under the 3:00 ceiling · 1280×720 · h264 + aac · 9.3 MB · English VO,
captions burned into the picture.)

1. Go to <https://studio.youtube.com> → **Create** → **Upload videos** → drop the file in.

2. **Title** (copy exactly):

```
SlateIQ — a day of dailies, turned into a database you can ask questions of
```

3. **Description** (copy the whole block, links included):

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

4. **Tags** (paste into the Tags box, comma-separated):

```
gemini, google adk, agent development kit, agent builder, vertex ai, clickhouse, mcp, model context protocol, mcp-clickhouse, cloud run, grafana, film production, dailies, script supervisor, hackathon, ai agents, google cloud
```

5. **Visibility: Public.** (Unlisted is accepted by the rules and is the safe fallback if you would
   rather it not be searchable — but *never* Private: judges must be able to open it. If you pick
   Unlisted, do **not** later flip it to Private.)

6. **Audience:** "No, it's not made for kids."

7. **Subtitles.** In the upload flow: **Show more → Subtitles → Add → Upload file → With timing →**
   select `video/CAPTIONS.srt`, language **English**. (The captions are also burned into the
   picture, so this is belt-and-braces for a judge whose player ignores tracks.)

8. **Category:** Science & Technology. **Comments:** leave on.

9. Publish, then copy the watch URL — it looks like `https://www.youtube.com/watch?v=XXXXXXXXXXX`.

10. **Open it in a private/incognito window and confirm it plays.** This is the one check that
    catches a video that is still processing or accidentally private.

---

## B — Paste the URL into the repo (4 edits, then push)

Let `YT` be your URL, e.g. `https://www.youtube.com/watch?v=XXXXXXXXXXX`.

### B1 — `README.md`, line 55

Replace this line:

```markdown
| **Video (≤3 min, YouTube)** | _uploading — the link lands here and in [`deploy/OUTPUT.md`](deploy/OUTPUT.md) before submission_ |
```

with:

```markdown
| **Video (≤3 min, YouTube)** | <https://www.youtube.com/watch?v=XXXXXXXXXXX> |
```

### B2 — `docs/SUBMISSION.md`, the **Video** row

Replace the `⚠️ **shot and committed, NOT uploaded**` cell with:

```markdown
| Video | ≤ 3 min, YouTube/Vimeo public, English | ✅ **uploaded** — 2:56, English VO + burned captions, `CAPTIONS.srt` attached as a subtitle track | https://www.youtube.com/watch?v=XXXXXXXXXXX |
```

…and delete "(1) the video is not uploaded;" from the **Top three remaining risks** line at the
bottom of that file.

### B3 — `docs/DEVPOST.md`, two occurrences of `VIDEO_URL`

Line 3 and line 186. Or just do it with one command:

```bash
cd /home/taitran/block
YT="https://www.youtube.com/watch?v=XXXXXXXXXXX"

# DEVPOST: both `VIDEO_URL` placeholders (line 3 and line 186)
sed -i "s|\`VIDEO_URL\`|<$YT>|g" docs/DEVPOST.md
# and line 3 now reads "Fill before submitting: <url>" — reword it by hand to "Video: <url>"

# README: the Live table row
sed -i "s|_uploading — the link lands here and in \[\`deploy/OUTPUT.md\`\](deploy/OUTPUT.md) before submission_|<$YT>|" README.md

# check all three landed
grep -n "youtube.com" README.md docs/DEVPOST.md docs/SUBMISSION.md
```

(`docs/SUBMISSION.md` still needs the hand edit in B2 — the sentence around it changes, not just
the URL.)

### B4 — commit and push

```bash
cd /home/taitran/block
git add README.md docs/DEVPOST.md docs/SUBMISSION.md
git commit -m "docs: video is live — YouTube URL in README, DEVPOST, SUBMISSION"
git push
```

Then reload <https://github.com/kaitorecca/slateiq> and click the video link from the rendered
README — one click proves the whole chain.

---

## C — The Devpost form, field by field

Hackathon: **Agentic Cinema: The Blockbuster Hackathon**. Submit to the **ClickHouse** partner track.

| Devpost field | What to enter |
|---|---|
| **Project name** | `SlateIQ` |
| **Elevator pitch / tagline** (≤ 60 chars) | `Dailies, turned into a database you can ask` **(43 chars)** |
| **Alternative tagline** if you prefer | `A day of dailies, as a queryable production brain` (49) · `Ask your dailies. Gemini + ClickHouse, live MCP.` (47) |
| **Description** (the long text box) | Paste **`docs/DEVPOST.md`** from the `## Inspiration` heading down to the end of `## Credits & licence`. Devpost's editor takes Markdown headings, bold, tables and links; paste the sections in this order, each as its own heading: **Inspiration · What it does · Why this doesn't already exist · How we built it · Challenges we ran into · What we learned · What's next · Credits & licence**. Do **not** paste the top three lines of the file (the "Live now / Fill before submitting" note) — that is an internal reminder, not submission copy. |
| **Built with** (tags) | `gemini`, `google-adk`, `vertex-ai`, `cloud-run`, `clickhouse`, `mcp`, `grafana`, `gcs`, `secret-manager`, `react`, `fastapi`, `ffmpeg` — add each, one at a time, pressing Enter between them. |
| **Partner track / category** | **ClickHouse** (tick it; if the form asks *how* the partner tech is used, answer: *"Every analytical answer is SQL the agent writes and executes through the official `mcp-clickhouse` MCP server at runtime — the specialists have no other data tool and there is no database driver on the reasoning path. 3.07 M rows of frame telemetry joined to Gemini's semantic output in 65 ms."*) |
| **"Try it out" / hosted URL** | `https://slateiq-957930801789.us-central1.run.app` |
| **Additional "Try it out" link** (if a second slot exists) | `https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health` |
| **Repository URL** | `https://github.com/kaitorecca/slateiq` |
| **Video demo URL** | your YouTube URL from §A |
| **Image gallery / thumbnail** | Upload `docs/img/ask.png` **first** (it becomes the card thumbnail — it shows the live MCP trace, which is the whole pitch), then `docs/img/trace.png`, `docs/img/takes.png`, `docs/img/health.png`. |
| **Team** | Solo — just you. Do not add anyone; team size ≤ 4 is satisfied trivially. |
| **Which Google Cloud / AI products** (if asked) | Gemini 3.5 Flash, Gemini 2.5 Flash TTS, Google Cloud Agent Development Kit (Agent Builder), Cloud Run, Cloud Storage, Secret Manager, Compute Engine, Artifact Registry, Cloud Build. |
| **Open-source licence** (if asked) | Apache-2.0 — <https://github.com/kaitorecca/slateiq/blob/main/LICENSE> |
| **Anything else / notes to judges** (if the form has one) | *"Cloud Run runs at `min-instances 0` on the free tier, so the very first request is a ~16 s cold start (the ADK import, not the database); everything after it is ~0.6 s. Best first question: 'Which circled takes are measurably soft?' — the trace panel shows the SQL going out through `mcp-clickhouse`."* |

**Save as draft as you go.** Devpost lets you edit a submission until the deadline; a saved draft
that you forget to *submit* does not count, so the last click must be **Submit**.

---

## D — Pre-submit verification (run these three, then submit)

```bash
cd /home/taitran/block

# 1 — the whole data plane: MCP health, 401 without a token, MCP handshake,
#     ClickHouse ping, row counts, agent_ro least privilege, Cloud Run /api/health.
#     Expect: ALL CHECKS PASSED
bash deploy/vm/healthcheck.sh

# 2 — the hosted agent, on its own. Expect "mcp":"up" and "clickhouse":"up".
#     Give it 60 s the first time — that is the documented cold start.
curl -s --max-time 90 https://slateiq-957930801789.us-central1.run.app/api/health | python3 -m json.tool

# 3 — the partner claim, end to end. Expect a tool_call named run_query carrying SQL.
curl -N --max-time 120 -X POST https://slateiq-957930801789.us-central1.run.app/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Which circled takes are measurably soft?"}'
```

Then, by eye:

- Open <https://slateiq-957930801789.us-central1.run.app> in an **incognito window** (no login, no
  cached session — that is what a judge sees). Click a suggested chip, watch the trace panel show
  `run_query · via mcp-clickhouse`. Check the header's green dot.
- Open the Grafana dashboard link in the same incognito window — all 8 panels should carry data.
- Open the YouTube link in that window and let it play a few seconds.
- Open the GitHub repo in that window: README renders, screenshots load, the video link works.

**Only after all four are green, press Submit on Devpost.** Target: at least a few hours before
07:00 AEST on 10 Sep — do not aim for the last minute; a cold start plus a form timeout is exactly
how a finished project misses a deadline.

---

## E — During the judging window (23 Sep – 7 Oct)

The judges open the hosted app themselves, so it has to be up. It costs almost nothing to leave it.

**Every few days, one command:**

```bash
bash /home/taitran/block/deploy/vm/healthcheck.sh
```

`ALL CHECKS PASSED` and you are done. If check 1 or 4 fails, the VM is down or the containers
stopped — the stack is a `systemd` unit (`slateiq-stack.service`, enabled), so a reboot fixes it:

```bash
gcloud compute instances start slateiq-data --zone us-central1-a   # if stopped
bash /home/taitran/block/deploy/vm/healthcheck.sh --ssh             # asks the VM about its containers
```

> ⚠️ **If the VM is ever stopped and restarted, its ephemeral external IP changes**, and the whole
> data plane is addressed as `<ip>.sslip.io`. Recovery is two idempotent scripts, ~4 minutes:
> `deploy/vm/deploy_stack.sh` (rewrites `.secrets/deploy.env`, re-issues the TLS cert) then
> `deploy/cloudrun/deploy_agent.sh` (re-points the agent). **So during the judging window, prefer
> to just leave the VM running.**

**What it costs to leave it running.** Everything is inside the Google Cloud Always Free tier
except one line: since 2020 Google bills **every** external IPv4 attached to a VM, ephemeral ones
included, at **$0.0035/hour ≈ $2.50/month**. From now through 7 Oct that is roughly **$2.60 total**,
and existing credits should absorb it. Cloud Run is `min-instances 0` on both services, so idle
costs nothing; the e2-micro, its 30 GB disk, the GCS bucket, Secret Manager and Cloud Build are all
free-tier. There is already a **$10/month budget alert** on the billing account — 4× headroom
before it fires. Full arithmetic: [`deploy/cost.md`](../deploy/cost.md).

**Consider `min-instances 1` for the judging window.** The ~16 s cold start is honest and
documented, but a judge who clicks once and waits may not click twice. If you decide the impression
is worth more than the free tier:

```bash
gcloud run services update slateiq --region us-central1 --min-instances 1   # leaves the free tier
# …and put it back on 8 Oct:
gcloud run services update slateiq --region us-central1 --min-instances 0
```

Ballpark for a warm 1 vCPU / 1 GiB instance held for ~15 days: **a few dollars**. Your call — the
README already tells the truth about the cold start either way.

**After 7 Oct**, to stop the last charge:

```bash
gcloud compute instances stop slateiq-data --zone us-central1-a
```

**Do not delete the VM.** It carries deletion protection and holds the seeded demo dataset.

---

## F — OPTIONAL stretch: a Grafana-track sibling submission

**This is entirely optional and nothing in the ClickHouse submission depends on it.** Do not start
it unless the ClickHouse submission is fully filed and there is real time left. It is roughly a
half-day of work — designed as an addition, not a redesign. Background:
[`deploy/README.md` §4, "Alternative for a Grafana-track sibling submission"](../deploy/README.md).

What it would require:

1. **A free Grafana Cloud account** — <https://grafana.com/auth/sign-up/create-user>. Free forever:
   10k series, 50 GB logs, 3 users. Create a stack, then a **service account token scoped to
   Viewer** (Administration → Service accounts).
2. **Recreate the Production Health dashboard on that stack**, pointed at the same ClickHouse
   (`https://35.239.36.85.sslip.io/ch`, user `agent_ro`) — install the
   `grafana-clickhouse-datasource` plugin there and import
   `deploy/grafana/dashboards/slateiq-production-health.json`.
3. **Attach [`grafana/mcp-grafana`](https://github.com/grafana/mcp-grafana) as a *second*
   `McpToolset`** on the ADK coordinator, beside `mcp-clickhouse` — not instead of it. It exposes
   `search_dashboards`, `get_dashboard_by_uid`, `list_datasources`, `list_alert_rules` and friends.
   The design line that makes the submission make sense: **`mcp-clickhouse` writes new analysis,
   `mcp-grafana` reuses existing analysis** — the report agent can cite a live panel URL instead of
   re-deriving the number.
4. **The demo beat:** ask *"are we on schedule?"*, and have the agent answer from ClickHouse **and**
   deep-link the live Production Health panel that proves it.
5. Cost stays $0 — Grafana Cloud free tier plus one more scale-to-zero Cloud Run revision.
6. A sibling Devpost submission would reuse everything in §C, swapping the partner track to
   **Grafana** and adding `grafana-cloud` and `mcp-grafana` to Built with. **Check the hackathon
   rules first** — some events forbid the same project entering two partner tracks. If they do,
   skip this entirely; the ClickHouse submission is the strong one.

---

## Quick reference

| Thing | Value |
|---|---|
| Video file | `video/slateiq_trailer_720p.mp4` — 2:56.1, 9.3 MB, 720p |
| Subtitle file | `video/CAPTIONS.srt` |
| Hosted app | <https://slateiq-957930801789.us-central1.run.app> |
| Grafana dashboard | <https://slateiq-grafana-hbissixc2q-uc.a.run.app/d/slateiq-prod-health> |
| Repo | <https://github.com/kaitorecca/slateiq> |
| MCP health (no auth) | <https://35.239.36.85.sslip.io/health> |
| Healthcheck | `bash deploy/vm/healthcheck.sh` |
| Submission text | [`docs/DEVPOST.md`](DEVPOST.md) |
| Beat-by-beat cut | [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| Status board | [`docs/SUBMISSION.md`](SUBMISSION.md) |
| Cost arithmetic | [`deploy/cost.md`](../deploy/cost.md) |
| GCP project / zone | `gke-hackathon-472816` · `us-central1-a` · VM `slateiq-data` |
| Deadline | **9 Sep 2026 14:00 PDT = 10 Sep 07:00 AEST** |
| Judging | **23 Sep – 7 Oct 2026** |
