"""
Kokoro TTS Service
CPU/GPU-safe, Windows-compatible, backend-friendly
"""

import logging
import torch
import tempfile
from pathlib import Path
from typing import Optional
import soundfile as sf

from kokoro import KPipeline

logger = logging.getLogger(__name__)


class KokoroTTSService:
    def __init__(self, lang_code: str = "a"):
        """
        lang_code:
        'a' => American English
        'b' => British English
        'h' => Hindi
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎙️ Initializing Kokoro on {self.device}")

        self.pipeline = KPipeline(lang_code=lang_code)

    def synthesize(
        self,
        text: str,
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        Generate speech and return WAV bytes
        """
        try:
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

            return data

        except Exception as e:
            logger.exception("❌ Kokoro TTS failed")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tts = KokoroTTSService(lang_code="h")  # Hindi
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
