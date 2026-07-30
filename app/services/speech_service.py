from typing import Optional

from app.core.config import get_settings
from app.core.logging import logger


class AudioSpeechService:
    """Service transcribing spoken narration and travel commentary from video audio tracks."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY

    async def transcribe_audio_speech(self, audio_bytes: Optional[bytes]) -> Optional[str]:
        """
        Transcribes speech from audio track bytes into text narration.
        """
        if not audio_bytes or len(audio_bytes) == 0:
            return None

        logger.info(f"Transcribing video audio track ({len(audio_bytes)} bytes)...")

        # In dev/mock testing mode
        if not self.api_key or self.api_key.startswith("your-") or self.api_key.startswith("mock-"):
            logger.info("Speech API key is unconfigured or mock. Returning fallback mock spoken transcription.")
            return "Exploring Fushimi Inari Shrine and cafes in Kyoto."

        # Production speech transcription logic
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Transcribe the spoken speech in this audio track accurately into clear English text."
                ]
            )
            transcription = response.text.strip()
            logger.info(f"Audio speech successfully transcribed ({len(transcription)} chars)")
            return transcription
        except Exception as e:
            logger.warning(f"Audio speech transcription failed: {str(e)}. Proceeding without speech transcription.")
            return None
