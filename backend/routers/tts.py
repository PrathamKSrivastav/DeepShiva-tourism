from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import logging
from utils.kokoro_service import KokoroTTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Preload two language pipelines (English 'a', Hindi 'h')
kokoro_en = KokoroTTSService(lang_code="a")
kokoro_hi = KokoroTTSService(lang_code="h")


@router.get("/tts/kokoro")
async def tts_kokoro(
    text: str = Query(..., min_length=1, max_length=2000),
    voice: str = Query("af_heart"),  # English voices: af_heart, am_fair, etc.
    lang: str = Query("a", regex="^(a|h)$"),  # 'a' English, 'h' Hindi
    speed: float = Query(1.0, ge=0.6, le=1.4),
):
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
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS service unavailable")
