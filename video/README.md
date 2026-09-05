# `video/` — the 3-minute SlateIQ trailer

Everything needed to regenerate `data/video/slateiq_trailer.mp4` from scratch. The
committed `slateiq_trailer_720p.mp4` next to this file is the upload copy (≤ 25 MB);
the 1080p master lives under `data/video/`, which is gitignored.

| File | What it is |
|---|---|
| `vo.json` | The voiceover script — one entry per beat, matching `docs/DEMO_SCRIPT.md`. |
| `tts.py` | Gemini TTS (`gemini-2.5-flash-preview-tts`, voice `Kore`) → `data/video/vo/*.wav`. Cached by text hash. |
| `capture.mjs` | Playwright screen capture of the real app and the rendered cards → `data/video/raw/*.webm` + `markers.json`. |
| `cards/` | The non-app beats (title, the arithmetic, ingest, the ClickHouse terminal, architecture, end card) as 1920×1080 HTML pages. |
| `build.py` | ffmpeg assembly: trims each scene to its own VO length, lays the narration down, burns the captions, writes the 720p copy. |
| `CAPTIONS.srt` | Sidecar captions (they are also burned into the picture). |

## Regenerate

```bash
# 0. prerequisites — the local stack must be up and seeded
docker start slateiq-ch && scripts/mcp_up.sh
set -a; source .env; set +a
uvicorn ... # or however agent/main.py is started; /api/health must report mcp+clickhouse up
curl -s localhost:8811/api/health

# 1. voiceover  (~1 min, cached — only re-synthesises beats whose text changed)
.venv/bin/python video/tts.py

# 2. screen capture  (~25 min — the agent really answers each question)
cd video && npm i && npx playwright install chromium && cd ..
# the card pages reference real clips/posters; these two symlinks are gitignored
ln -sfn ../../data/clips  video/cards/clips
ln -sfn ../../data/thumbs video/cards/thumbs
node video/capture.mjs                  # all scenes
node video/capture.mjs hero dpr         # just these

# 3. assemble
.venv/bin/python video/build.py         # add --fast while iterating on the cut

# 4. QC
.venv/bin/python video/qc.py
```

## Notes that will bite you

- **Chromium.** `capture.mjs` falls back to any `chromium-*` build already in
  `~/.cache/ms-playwright` when `npx playwright install` can't reach the network.
  Override with `SLATEIQ_CHROME=/path/to/chrome`.
- **Capture is 25 fps**, real-time and frame-accurate; `build.py` conforms
  everything to 30 fps. Playwright's webm container duration is unreliable — always
  count frames (`probe()` does).
- **The cut is pinned to VO length, not to the footage.** Each beat is trimmed to
  its narration; if a scene came up short its last frame is held. So re-recording a
  scene at a different length does not require re-timing the edit.
- **In-points are symbolic** (`ANSWER-4`, `TAIL`, `HERO_IN`) and resolve against the
  scene's real duration, for the same reason.
- **`SLATEIQ_URL`** defaults to `http://localhost:8811` (identical build to Cloud Run,
  much faster). The `live` scene always drives the hosted Cloud Run service on
  purpose — the closing beat has to be the deployed app.
- **Beats 8 and 9 are recorded against the hosted Cloud Run service on purpose.**
  Grafana is only wired up there (via `/api/config`), so the local build would have
  shown the in-app fallback charts under a voiceover promising Grafana. Those
  `d-solo` iframes never reach `networkidle` and take ~20 s to paint.
- **Every number spoken is a live query result.** If the dataset is reseeded, re-run
  the golden queries, fix `vo.json` and `cards/*.html`, and re-synthesise. Do not let
  a stale figure survive into the edit.
- **The 4-second full-frame hold on the MCP trace is not optional** — it is the
  Stage-1 "partner used at runtime" evidence frame. `traceFullFrame()` in
  `capture.mjs` produces it, and `markers.json` records exactly where it lands.

## Credits

Footage: *Tears of Steel* © Blender Foundation, CC BY 3.0 — mango.blender.org.
