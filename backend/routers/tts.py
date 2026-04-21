from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import logging
from utils.kokoro_service import KokoroTTSService, KOKORO_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-instantiated pipelines. Eager init at module import time previously
# crashed the container because KokoroTTSService() loads a ~300 MB model from
# HuggingFace Hub and mkdirs a cache directory under the non-root app user —
# both can fail and take uvicorn's port bind down with them. First request to
# /tts/kokoro now pays the one-time ~30 s warm-up cost.
_kokoro_en: "KokoroTTSService | None" = None
_kokoro_hi: "KokoroTTSService | None" = None


def _get_pipeline(lang: str) -> "KokoroTTSService | None":
    global _kokoro_en, _kokoro_hi
    if not KOKORO_AVAILABLE:
        return None
    if lang == "a":
        if _kokoro_en is None:
            _kokoro_en = KokoroTTSService(lang_code="a")
        return _kokoro_en
    if _kokoro_hi is None:
        _kokoro_hi = KokoroTTSService(lang_code="h")
    return _kokoro_hi


def _unavailable():
    raise HTTPException(
        status_code=503,
        detail="TTS service is not available on this deployment (kokoro/torch not installed)",
    )


@router.get("/tts/kokoro")
async def tts_kokoro(
    text: str = Query(..., min_length=1, max_length=2000),
    voice: str = Query("af_heart"),
    lang: str = Query("a", regex="^(a|h)$"),
    speed: float = Query(1.0, ge=0.6, le=1.4),
):
    if not KOKORO_AVAILABLE:
        _unavailable()

    try:
        svc = _get_pipeline(lang)
        if svc is None:
            _unavailable()
        audio_bytes = svc.synthesize(text=text, voice=voice, speed=speed)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Kokoro synthesis failed")

        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/wav",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS service unavailable")


@router.get("/tts/status")
async def tts_status():
    return {
        "available": KOKORO_AVAILABLE,
        "message": "TTS ready" if KOKORO_AVAILABLE else "TTS not available on this deployment",
    }
