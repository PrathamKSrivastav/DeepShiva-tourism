"""
Audio Processing with faster-whisper
Transcribes audio to text and detects language (English/Hindi)
"""

import logging
import os
import tempfile
from typing import Dict, Tuple
from faster_whisper import WhisperModel
from pydub import AudioSegment
import langdetect
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process audio files and transcribe to text"""
    
    def __init__(self):
        """Initialize faster-whisper model"""
        try:
            # Use small model with int8 quantization for speed and efficiency
            logger.info("🎤 Loading faster-whisper model (small, int8)...")
            self.model = WhisperModel(
                "small",
                device="cpu",  # Use "cuda" if you have GPU
                compute_type="int8"
            )
            logger.info("✅ Audio model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load audio model: {str(e)}")
            self.model = None
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        detect_language: bool = True
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            detect_language: Whether to detect language
            
        Returns:
            {
                "transcription": "text",
                "detected_language": "en/hi",
                "confidence": 0.95
            }
        """
        if not self.model:
            raise Exception("Audio model not initialized")
        
        try:
            logger.info(f"🎤 Transcribing audio: {audio_file_path}")
            
            # Convert audio to WAV if needed
            audio_path = await self._prepare_audio(audio_file_path)
            
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_path,
                language=None if detect_language else "en",
                beam_size=5,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    min_silence_duration_ms=500
                )
            )
            
            # Collect transcription
            transcription_text = " ".join([segment.text for segment in segments]).strip()
            
            # Detect language (faster-whisper provides this)
            detected_lang = info.language if detect_language else "en"
            detected_lang_code = self._map_language_code(detected_lang)
            
            # Additional language detection for Hindi/Hinglish
            if detected_lang_code == "hi" or self._contains_hindi_words(transcription_text):
                detected_lang_code = "hi"
            
            logger.info(f"✅ Transcription complete")
            logger.info(f"   Text: {transcription_text[:100]}...")
            logger.info(f"   Detected Language: {detected_lang_code}")
            logger.info(f"   Confidence: {info.language_probability}")
            
            # Cleanup temp files
            if audio_path != audio_file_path:
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            return {
                "transcription": transcription_text,
                "detected_language": detected_lang_code,
                "confidence": info.language_probability,
                "duration": info.duration
            }
            
        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    async def _prepare_audio(self, audio_path: str) -> str:
        """
        Convert audio to WAV format if needed
        faster-whisper works best with WAV
        """
        file_ext = Path(audio_path).suffix.lower()
        
        # Already WAV, no conversion needed
        if file_ext == ".wav":
            return audio_path
        
        try:
            logger.info(f"🔄 Converting {file_ext} to WAV...")
            
            # Load audio with pydub
            if file_ext == ".webm":
                audio = AudioSegment.from_file(audio_path, format="webm")
            elif file_ext == ".mp3":
                audio = AudioSegment.from_mp3(audio_path)
            elif file_ext == ".ogg":
                audio = AudioSegment.from_ogg(audio_path)
            elif file_ext == ".m4a":
                audio = AudioSegment.from_file(audio_path, format="m4a")
            else:
                # Try generic loader
                audio = AudioSegment.from_file(audio_path)
            
            # Convert to mono 16kHz (optimal for Whisper)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Save as temporary WAV
            temp_wav = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            )
            audio.export(temp_wav.name, format="wav")
            
            logger.info(f"✅ Converted to WAV: {temp_wav.name}")
            return temp_wav.name
            
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {str(e)}")
            # Return original if conversion fails
            return audio_path
    
    def _map_language_code(self, lang: str) -> str:
        """Map Whisper language codes to our system"""
        lang_mapping = {
            "english": "en",
            "en": "en",
            "hindi": "hi",
            "hi": "hi",
            # Add more if needed
        }
        return lang_mapping.get(lang.lower(), "en")
    
    def _contains_hindi_words(self, text: str) -> bool:
        """
        Detect if text contains Hindi/Devanagari characters
        or common Hinglish patterns
        """
        try:
            # Check for Devanagari Unicode range
            for char in text:
                if '\u0900' <= char <= '\u097F':
                    return True
            
            # Use langdetect for mixed language
            detected = langdetect.detect(text)
            if detected == "hi":
                return True
                
        except:
            pass
        
        return False


# Singleton instance
_audio_processor = None

def get_audio_processor() -> AudioProcessor:
    """Get or create audio processor instance"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor
