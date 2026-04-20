"""
Kokoro TTS Service
CPU/GPU-safe, Windows-compatible, backend-friendly
Lazy imports so the server starts even when torch/kokoro are not installed.
"""

import logging
import tempfile
import hashlib
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Check once at module load whether the heavy deps are present
try:
    import torch
    from kokoro import KPipeline
    import soundfile as sf
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    logger.warning("⚠️ Kokoro TTS unavailable (torch/kokoro not installed)")


class KokoroTTSService:
    def __init__(self, lang_code: str = "a"):
        """
        lang_code:
        'a' => American English
        'b' => British English
        'h' => Hindi
        """
        if not KOKORO_AVAILABLE:
            self.available = False
            logger.warning("⚠️ KokoroTTSService created but kokoro is not installed")
            return

        self.available = True
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎙️ Initializing Kokoro on {self.device}")
        self.lang_code = lang_code

        self.pipeline = KPipeline(lang_code=lang_code)
        self.cache_dir = Path(__file__).parent.parent / "cache" / "tts"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """Generate speech and return WAV bytes. Returns None if unavailable."""
        if not getattr(self, "available", False):
            return None

        try:
            key = f"{self.lang_code}|{voice}|{speed}|{text}"
            key_hash = hashlib.sha1(key.encode("utf-8")).hexdigest()
            cache_path = self.cache_dir / f"{key_hash}.wav"

            if cache_path.exists():
                logger.debug(f"🗄️ TTS cache hit: {key_hash}")
                return cache_path.read_bytes()
            logger.debug(f"🆕 TTS cache miss: {key_hash}")

            generator = self.pipeline(
                text,
                voice=voice,
                speed=speed,
                split_pattern=r"\n+",
            )

            audio_chunks = []
            sample_rate = 24000

            for _, _, audio in generator:
                audio_chunks.append(audio)

            if not audio_chunks:
                return None

            audio = torch.cat(audio_chunks).cpu().numpy()

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, audio, sample_rate)
                wav_path = f.name

            data = Path(wav_path).read_bytes()
            Path(wav_path).unlink()

            try:
                cache_path.write_bytes(data)
            except Exception as ce:
                logger.warning(f"⚠️ Could not write TTS cache: {ce}")

            return data

        except Exception:
            logger.exception("❌ Kokoro TTS failed")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tts = KokoroTTSService(lang_code="h")
    audio = tts.synthesize(
        "Hey this is a test for text to speech",
        voice="hf_alpha",
        speed=1.0,
    )

    if audio:
        Path("test_kokoro.wav").write_bytes(audio)
        print("✅ Audio written to test_kokoro.wav")
    else:
        print("❌ TTS failed")
