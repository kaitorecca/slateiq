# Clean-clone reproducibility test

**What this is.** A judge clones `https://github.com/kaitorecca/slateiq`, follows README
*"Run it locally"* and the `Makefile`, and nothing else. This is that run, simulated on the dev box
on **2026-09-05** against an **isolated** second stack so the live demo stack was never touched.

Everything below was executed, not reasoned about. Eight defects were found; all eight are fixed and
re-verified from a second, brand-new clone.

---

## Isolation

The live stack (`slateiq-ch` on 8123, MCP 8765, API 8811) kept running throughout and was
re-checked at the end. The test stack used:

| | live | test |
|---|---|---|
| ClickHouse | `slateiq-ch` :8123 | `slateiq-ch-test` :28123 |
| mcp-clickhouse | :8765 | :28765 |
| API | :8811 | :28811 |

> The brief asked for 18123/18765/18811. **18123 was already taken** by an unrelated
> `densery-clickhouse-1` container, so the test moved to the 28xxx block. That is itself the first
> evidence for the finding below: a port collision is a normal thing to hit, and the stack has to be
> movable.

---

## Timings

Two clones. **Clone 1** followed the README *as it was* and is where the defects surfaced.
**Clone 2** was a fresh clone of the *fixed* repo, run start to finish with no manual repair.

### Clone 2 — the fixed path, end to end

| Step | Command | Time | Result |
|---|---|---:|---|
| clone | `git clone …` | 9.8 s | ok |
| venvs | `make venvs` | 34.1 s | both venvs, all requirements |
| env | `cp .env.example .env` + paste key | — | ok |
| seed | `db/generate_synthetic.py --reset` | 3.4 s | 2,479 takes · 3,066,358 telemetry rows |
| verify | `db/verify.py` | 0.9 s | **43/43 passed** |
| tests | `pytest agent/tests -q` | 2.8 s | **116 passed** |
| lint | `make lint` | 1.3 s | ruff clean |

**Under 55 seconds from `git clone` to a verified database**, on top of a `docker run` for
ClickHouse and a Gemini key.

### Clone 1 — the service layer

| Step | Command | Time | Result |
|---|---|---:|---|
| MCP up | `CLICKHOUSE_MCP_BIND_PORT=28765 scripts/mcp_up.sh` | ~3 s | `/health` → `OK` |
| API up | `make api API_PORT=28811` | ~8 s | `/api/health` → `mcp:up`, `clickhouse:up` |
| health | `curl /api/health` | 26 ms | pointed at `:28765` / `:28123`, `web_dist:true` |
| chat | `POST /api/chat` "Are we on schedule after day 12?" | **59.1 s** | coordinator → `production_agent`, **11 `run_query` calls through mcp-clickhouse**, 18.9 kB SSE, `type:final` |
| web deps | `npm ci` | 3.3 s | ok |
| web build | `npm run build` | 7.4 s | ✓ built in 3.66 s, 6 chunks |

The committed `web/dist` means the API serves the real SPA before `npm` is ever run.

---

## Findings

Ordered by how hard they stop a judge. All eight fixed in
`2f21323` and `bc20eb3`; no product behaviour changed.

### P1 — the documented setup did not reach step 3

`README` step 2 installed **only** `agent/requirements.txt`. But `db/generate_synthetic.py` imports
`numpy` and `pyarrow`, and `ingest/telemetry.py` imports `numpy` — none of which were in any
requirements file anywhere in the repo.

```
ModuleNotFoundError: No module named 'numpy'
```

That is the **third command in the README**, and it failed. **Fix:** new `ingest/requirements.txt`
(the data-pipeline deps, kept out of `agent/requirements.txt` so the Cloud Run image does not grow),
wired into the README step and a new `make venvs`.

### P1 — `make test` could not run

`pytest` and `ruff` were installed ad-hoc on the dev box and appear in no requirements file, so the
Makefile target the README advertises as *"unit tests (116, no network, no ClickHouse)"* died with
`No module named pytest`. **Fix:** new `requirements-dev.txt`, also in `make venvs`.

### P1 — no `.env.example`

The README told you to hand-write `.env` from a heredoc. The heredoc **omitted `CLICKHOUSE_SECURE`**,
and `mcp-clickhouse` 0.6.0 defaults it to `true` — so following the README literally produced:

```
$ curl localhost:28765/health
ERROR. ClickHouse connection failed. Check server logs for details.
```

against a perfectly healthy local ClickHouse, with no hint as to why. **Fix:** `.env.example`
documenting every variable the code actually reads (including `CLICKHOUSE_SECURE`,
`CLICKHOUSE_MCP_BIND_PORT`, the `FFMPEG_BIN` overrides and the Vertex block), and the README now
says `cp .env.example .env`.

### P1 — the MCP port could not be overridden

`scripts/mcp_up.sh` **hard-exported** `CLICKHOUSE_MCP_BIND_PORT=8765` after sourcing `.env`, so
neither the environment nor `.env` could move it. With 8765 already in use it simply died:

```
ERROR: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8765): address already in use
```

Anyone whose 8765 is taken — and anyone wanting two stacks — was stuck. **Fix:** every
`CLICKHOUSE_MCP_*` variable now falls back with `:=` instead of being overwritten,
`CLICKHOUSE_MCP_ALLOWED_HOSTS` follows the chosen port automatically, and the script logs the URL it
is binding. `make mcp MCP_PORT=…` passes it through. Verified: both MCP servers ran side by side,
`/health` → `OK` on 8765 **and** 28765.

### P1 — `ingest/` hard-coded the author's laptop

```python
FFMPEG = os.environ.get("FFMPEG_BIN", str(Path.home() / "miniconda3/envs/media/bin/ffmpeg"))
```

A path that exists on exactly one machine on earth. A judge with a normal `apt install ffmpeg` got
`ffmpeg not found at /home/<them>/miniconda3/envs/media/bin/ffmpeg`. **Fix:** `shutil.which("ffmpeg")`,
with the `FFMPEG_BIN` / `FFPROBE_BIN` overrides kept.

### P1 — `ingest/run_all.sh` cannot run from a clean clone, and the docs pointed in a circle

This is the honest one. The README presented the ingest replay as a normal step:

```
./ingest/run_all.sh    # replays from data/cache/
```

On a clean clone it stops on the first line:

```
== 1/5 cut clips ==
missing source footage …/data/footage/tos.mp4
```

`data/cache/` **is** committed and complete (26 files, identical in the clone), but it is keyed by
**the SHA-1 of each cut clip** — and the clips are gitignored, and they are cut from a 355 MB source
file that is also not committed. So the cache cannot be replayed without first reproducing the exact
clips. `README` → *"download it yourself, see `ingest/README.md`"* → `ingest/README.md` → attribution
only, **no URL**. A closed loop with no exit.

**Fix — documented precisely rather than faked.** Making the loader work from cache alone would mean
committing a clip manifest *and* pre-computed telemetry (`frame_telemetry` is derived from the clip
bytes by ffmpeg), i.e. changing what the pipeline actually proves. Instead the source file was
identified exactly: it is byte-identical to Blender's published `tears_of_steel_720p.mov` —
**372,178,639 bytes, md5 `8821bfe2b76c5c303ae0990a22f8802d`** — verified by `content-length` against
the mirror. All three READMEs now carry the real `curl` command and the md5, state that any *other*
encode misses the cache keys and silently falls back to **live, billable Gemini calls**, and point at
`python ingest/analyze.py --dry-run` to check cache state before spending anything.

Most importantly the README now says the thing that was never written down: **the ingest slice is
optional.** `db/generate_synthetic.py` alone satisfies **all 43** `db/verify.py` checks and runs the
entire agent stack — confirmed here, twice, with no footage on disk. The section is now a collapsed
*"Optional — rebuilding the real day-12 dailies slice"*.

### P2 — ports were undocumented as overridable

The README listed the four ports as facts. `CLICKHOUSE_PORT`, `CLICKHOUSE_MCP_URL` and
`make api API_PORT=` all worked already; `CLICKHOUSE_MCP_BIND_PORT` did not (above). **Fix:** the
ports note now says which variables move them and that the MCP bind port and `CLICKHOUSE_MCP_URL`
must be kept in step.

### P3 — `make lint` failed on a clean clone

`cd web && npx tsc --noEmit` with no `web/node_modules` makes `npx` offer to *download* TypeScript,
then fails the target. **Fix:** the tsc step is now guarded on `web/node_modules` and prints
`skipping tsc --noEmit: run 'cd web && npm ci' first`. Both branches verified.

---

## What was already right

Worth recording, because it is most of the repo:

- `db/generate_synthetic.py`, `db/verify.py` and `ingest/load.py` **all** read `CLICKHOUSE_HOST` /
  `PORT` / `USER` / `PASSWORD` / `SECURE` with sensible defaults. The seed landed in the test
  container on 28123 first try.
- `make api API_PORT=28811` worked unmodified, and `agent/slateiq_agent/config.py` honours
  `CLICKHOUSE_MCP_URL`, so the agent talked to the *test* MCP with no code change.
- `data/cache/` is genuinely complete and byte-identical between the working tree and the clone —
  the replay-for-free claim holds, given the footage.
- `web/dist` is committed, so the API serves the real UI before `npm` runs.
- 116 tests pass with no network and no ClickHouse, as advertised. `ruff check` clean.
- Python **3.13** was used throughout although the README says 3.12; everything worked.
- No secrets in the clone. The real key was supplied only through an untracked local `.env`.

## Not covered

`make eval` (28 judged questions, real Gemini spend), `make deploy`, and the ingest pipeline past
its first line — that last one needs the 355 MB download, which is exactly the finding.

## Cleanup

`slateiq-ch-test` stopped and removed; the two test processes killed by pid; `data/` untouched.
Live stack re-verified afterwards: `:8123`, `:8765` `/health` **OK**, `:8811` `/api/health`
**`mcp:up` / `clickhouse:up`**.
