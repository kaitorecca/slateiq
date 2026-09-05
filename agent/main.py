"""SlateIQ FastAPI app.

Built on ADK's `get_fast_api_app` (so the ADK dev UI and the standard
/run, /run_sse, /apps/... endpoints come for free) plus SlateIQ's own
UI-facing routes:

  GET  /api/health          -- liveness + MCP/model config
  POST /api/chat            -- SSE stream: text, tool_call, tool_result, final
  GET  /api/report/dpr      -- Daily Progress Report markdown for a day
  GET  /api/report/editor-log
  POST /api/tts             -- Gemini TTS wav of a <=90 word spoken summary
  GET  /api/takes           -- convenience passthrough for the takes gallery
  GET  /api/take/{id}/events -- transcript + flag timeline for one take
  GET  /clips/...           -- local clip files
  GET  /                    -- web/dist if it has been built

IMPORTANT: all *agent reasoning* goes through the ClickHouse MCP server
(`slateiq_agent.agent.clickhouse_toolset`). The only direct clickhouse-connect
usage in this file is `/api/takes`, a dumb listing endpoint for the gallery --
it does no reasoning and is clearly marked below.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import struct
import sys
from pathlib import Path
from typing import Any, Optional

# Make the package importable when uvicorn is started from agent/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import HTTPException, Query, Request  # noqa: E402
from fastapi.responses import (  # noqa: E402
    FileResponse,
    JSONResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402
from google.adk.cli.fast_api import get_fast_api_app  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from slateiq_agent import config  # noqa: E402
from slateiq_agent.runtime import run_once, stream_agent  # noqa: E402
from slateiq_agent.schema import schema_source  # noqa: E402

logging.basicConfig(level=os.environ.get("SLATEIQ_LOG_LEVEL", "INFO"))
logger = logging.getLogger("slateiq.api")

AGENT_DIR = str(Path(__file__).resolve().parent)

app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    allow_origins=["*"],
    session_service_uri=config.SESSION_DB_URI,
)
app.title = "SlateIQ"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": "slateiq",
        "model": config.MODEL,
        "report_model": config.REPORT_MODEL,
        "tts_model": config.TTS_MODEL,
        "clickhouse_mcp_url": config.MCP_URL,
        "clickhouse_mcp_auth": bool(config.MCP_TOKEN),
        "database": config.DB,
        "schema_source": schema_source(),
        "web_dist": Path(config.WEB_DIST).is_dir(),
        "clips_dir": Path(config.CLIPS_DIR).is_dir(),
    }


# ---------------------------------------------------------------------------
# Chat (SSE)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    user_id: str = "web"
    agent: str = "coordinator"


def _sse(event: dict[str, Any]) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, default=str)}\n\n"


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    """Stream the agent run as SSE so the UI can show the live SQL trace."""

    async def gen():
        try:
            async for event in stream_agent(
                req.message,
                user_id=req.user_id,
                session_id=req.session_id,
                agent_key=req.agent,
            ):
                if await request.is_disconnected():
                    break
                yield _sse(event)
        except Exception as exc:  # pragma: no cover
            logger.exception("chat stream failed")
            yield _sse({"type": "error", "message": str(exc)})
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
_DPR_PROMPT = (
    "Generate the DAILY PROGRESS REPORT for shooting day {day}. Query the "
    "database for the production title and total days, the shooting day's "
    "call/wrap times and planned scenes, every scene shot that day with its "
    "pages, takes, setups and status, and the day + cumulative totals. Output "
    "the finished Markdown document only."
)

_LOG_PROMPT = (
    "Generate the EDITOR'S LOG for shooting day {day}: every scene shot that "
    "day, its takes with shot, take number, timecode in, duration and status, "
    "and for each scene the circled take(s) with the reason they were circled "
    "(director note or analysis reason). Output the finished Markdown only."
)


async def _report(prompt: str, day: int) -> dict[str, Any]:
    result = await run_once(
        prompt.format(day=day), user_id="report", agent_key="report"
    )
    if result.get("error"):
        raise HTTPException(502, result["error"])
    return {
        "day": day,
        "markdown": result["text"],
        "sql": result["sql"],
        "tool_calls": len(result["tool_calls"]),
        "ran_query": result["ran_query"],
    }


@app.get("/api/report/dpr")
async def dpr(day: int = Query(..., ge=1, le=365)) -> dict[str, Any]:
    return await _report(_DPR_PROMPT, day)


@app.get("/api/report/editor-log")
async def editor_log(day: int = Query(..., ge=1, le=365)) -> dict[str, Any]:
    return await _report(_LOG_PROMPT, day)


# ---------------------------------------------------------------------------
# Text to speech (Gemini)
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice: Optional[str] = None
    summarize: bool = True


def _pcm_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1, width: int = 2) -> bytes:
    """Gemini TTS returns raw little-endian PCM; wrap it in a WAV container."""
    buf = io.BytesIO()
    data_len = len(pcm)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_len))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, channels, rate,
                          rate * channels * width, channels * width, width * 8))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_len))
    buf.write(pcm)
    return buf.getvalue()


def _rate_from_mime(mime: str) -> int:
    for part in (mime or "").split(";"):
        part = part.strip()
        if part.startswith("rate="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                pass
    return 24000


@app.post("/api/tts")
async def tts(req: TTSRequest) -> Response:
    """Speak a <=90 word summary of the given text with Gemini TTS."""
    from google import genai
    from google.genai import types as gtypes

    client = genai.Client()
    text = req.text.strip()

    if req.summarize and len(text.split()) > 90:
        try:
            condensed = await client.aio.models.generate_content(
                model=config.MODEL,
                contents=(
                    "Rewrite this film-production update as a spoken briefing "
                    "for the producer. Maximum 90 words, plain sentences, no "
                    "markdown, no lists, no symbols. Keep every number.\n\n"
                    + text
                ),
            )
            if condensed.text:
                text = condensed.text.strip()
        except Exception:
            logger.warning("TTS summarisation failed; speaking raw text")
            text = " ".join(text.split()[:90])

    try:
        resp = await client.aio.models.generate_content(
            model=config.TTS_MODEL,
            contents=text,
            config=gtypes.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=gtypes.SpeechConfig(
                    voice_config=gtypes.VoiceConfig(
                        prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(
                            voice_name=req.voice or config.TTS_VOICE
                        )
                    )
                ),
            ),
        )
    except Exception as exc:
        raise HTTPException(502, f"TTS failed: {exc}") from exc

    try:
        part = resp.candidates[0].content.parts[0].inline_data
        raw = part.data
        if isinstance(raw, str):
            raw = base64.b64decode(raw)
        mime = part.mime_type or ""
    except Exception as exc:
        raise HTTPException(502, f"TTS returned no audio: {exc}") from exc

    if "wav" in mime:
        audio, media = raw, "audio/wav"
    elif "mp3" in mime or "mpeg" in mime:
        audio, media = raw, "audio/mpeg"
    else:  # raw PCM (audio/L16;codec=pcm;rate=24000)
        audio, media = _pcm_to_wav(raw, _rate_from_mime(mime)), "audio/wav"

    return Response(
        content=audio,
        media_type=media,
        headers={
            "Content-Disposition": 'inline; filename="slateiq.wav"',
            "X-SlateIQ-Spoken-Words": str(len(text.split())),
        },
    )


# ---------------------------------------------------------------------------
# Takes passthrough
#
# NOTE: this is the ONLY direct-ClickHouse endpoint. It exists so the takes
# gallery can page through rows without paying for an LLM turn. No agent
# reasoning happens here -- every analytical answer goes through MCP.
# ---------------------------------------------------------------------------
def _ch_client():
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        secure=os.environ.get("CLICKHOUSE_SECURE", "false").lower() == "true",
    )


@app.get("/api/takes")
async def takes(
    scene: Optional[str] = None,
    day: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
) -> JSONResponse:
    """Direct ClickHouse listing for the UI gallery (not agent reasoning).

    Returns the fields the takes gallery renders: identity, status, media URIs,
    duration, the analysis quality score/summary and the distinct flag types.
    """
    where, params = ["1"], {"limit": limit}
    if scene:
        where.append("t.scene_number = %(scene)s")
        params["scene"] = str(scene)
    if day is not None:
        where.append("t.day_number = %(day)s")
        params["day"] = day
    if status:
        where.append("t.status = %(status)s")
        params["status"] = status
    sql = f"""
        SELECT t.take_id AS take_id, t.day_number, t.scene_number, t.shot, t.take_number,
               t.camera, t.roll, t.tc_in, t.duration_s, t.status,
               t.director_note, t.clip_uri, t.thumb_uri,
               a.quality_score, a.summary, a.recommended, a.emotion_intensity,
               f.flags
        FROM {config.DB}.take t
        LEFT JOIN {config.DB}.take_analysis a USING (take_id)
        LEFT JOIN (
            SELECT take_id, groupUniqArray(flag_type) AS flags
            FROM {config.DB}.take_event
            WHERE kind = 'flag' AND flag_type != ''
            GROUP BY take_id
        ) f USING (take_id)
        WHERE {' AND '.join(where)}
        ORDER BY t.day_number, t.scene_number, t.shot, t.take_number
        LIMIT %(limit)s
    """
    try:
        res = _ch_client().query(sql, parameters=params)
        rows = [dict(zip(res.column_names, r)) for r in res.result_rows]
    except Exception as exc:
        raise HTTPException(502, f"ClickHouse query failed: {exc}") from exc
    for r in rows:
        r["flags"] = list(r.get("flags") or [])
        r["quality_score"] = (
            float(r["quality_score"]) if r.get("quality_score") is not None else None
        )
    return JSONResponse(
        {
            "count": len(rows),
            "source": "direct clickhouse-connect (UI listing only)",
            "takes": json.loads(json.dumps(rows, default=str)),
        }
    )


@app.get("/api/take/{take_id}/events")
async def take_events(take_id: str, limit: int = Query(500, ge=1, le=2000)) -> JSONResponse:
    """Transcript + flag timeline for one take (UI detail pane)."""
    try:
        client = _ch_client()
        head = client.query(
            f"""SELECT t.take_id AS take_id, t.day_number, t.scene_number, t.shot,
                       t.take_number, t.camera, t.tc_in, t.duration_s, t.status,
                       t.director_note, t.clip_uri, t.thumb_uri,
                       a.summary, a.transcript, a.quality_score,
                       a.recommended, a.emotion_intensity, a.performance_note
                FROM {config.DB}.take t
                LEFT JOIN {config.DB}.take_analysis a USING (take_id)
                WHERE t.take_id = %(id)s LIMIT 1""",
            parameters={"id": take_id},
        )
        if not head.result_rows:
            raise HTTPException(404, f"take '{take_id}' not found")
        take = dict(zip(head.column_names, head.result_rows[0]))
        ev = client.query(
            f"""SELECT event_id, t_offset_s, t_end_s, kind, speaker, text,
                       flag_type, severity, score
                FROM {config.DB}.take_event
                WHERE take_id = %(id)s
                ORDER BY t_offset_s LIMIT %(lim)s""",
            parameters={"id": take_id, "lim": limit},
        )
        events = [dict(zip(ev.column_names, r)) for r in ev.result_rows]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"ClickHouse query failed: {exc}") from exc

    payload = {
        "take": take,
        "events": events,
        "dialogue": [e for e in events if e["kind"] == "dialogue"],
        "flags": [e for e in events if e["kind"] == "flag"],
        "source": "direct clickhouse-connect (UI detail only)",
    }
    return JSONResponse(json.loads(json.dumps(payload, default=str)))


# ---------------------------------------------------------------------------
# Static media + web UI
# ---------------------------------------------------------------------------
_clips = Path(config.CLIPS_DIR)
if _clips.is_dir():
    app.mount("/clips", StaticFiles(directory=str(_clips)), name="clips")
    logger.info("Serving clips from %s", _clips)
else:
    logger.warning("CLIPS_DIR %s does not exist -- /clips not mounted", _clips)

_dist = Path(config.WEB_DIST)
if _dist.is_dir():
    # ADK registers a `/` route that redirects to its dev UI. The SlateIQ web
    # app owns the site root, so drop that route before mounting; the ADK dev
    # UI stays reachable at /dev-ui/.
    app.router.routes = [
        r for r in app.router.routes if getattr(r, "path", None) != "/"
    ]
    class _SpaStatic(StaticFiles):
        """StaticFiles that falls back to index.html for client-side routes."""

        async def get_response(self, path: str, scope):  # type: ignore[override]
            try:
                return await super().get_response(path, scope)
            except StarletteHTTPException as exc:
                if exc.status_code == 404 and not path.startswith("assets/"):
                    return await super().get_response("index.html", scope)
                raise

    # Mounted last so /api/* and the ADK routes registered above still win.
    app.mount("/", _SpaStatic(directory=str(_dist), html=True), name="web")
    logger.info("Serving web UI from %s", _dist)
else:
    logger.warning("web/dist not built at %s -- ADK dev UI remains at /dev-ui", _dist)

    @app.get("/api/ui-status")
    async def ui_status() -> dict[str, Any]:
        return {"web_dist": False, "path": str(_dist),
                "hint": "build web/ then restart, or use the ADK dev UI"}
