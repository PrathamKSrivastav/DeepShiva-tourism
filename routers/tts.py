from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import logging
from utils.kokoro_service import KokoroTTSService, KOKORO_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()

# Only instantiate pipelines when the packages are present
if KOKORO_AVAILABLE:
    kokoro_en = KokoroTTSService(lang_code="a")
    kokoro_hi = KokoroTTSService(lang_code="h")
else:
    kokoro_en = None
    kokoro_hi = None


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
    if not KOKORO_AVAILABLE or kokoro_en is None:
        _unavailable()

    try:
        svc = kokoro_en if lang == "a" else kokoro_hi
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
