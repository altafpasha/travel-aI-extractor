import pytest
from app.services.speech_service import AudioSpeechService


@pytest.mark.asyncio
async def test_transcribe_audio_speech_none_input():
    """Tests that empty audio bytes return None cleanly."""
    service = AudioSpeechService()
    result = await service.transcribe_audio_speech(None)
    assert result is None

    result_empty = await service.transcribe_audio_speech(b"")
    assert result_empty is None


@pytest.mark.asyncio
async def test_transcribe_audio_speech_mock():
    """Tests audio transcription fallback in test environment."""
    service = AudioSpeechService(api_key="mock-key")
    dummy_wav_bytes = b"RIFF" + b"\x00" * 100
    transcript = await service.transcribe_audio_speech(dummy_wav_bytes)

    assert transcript is not None
    assert isinstance(transcript, str)
    assert "Fushimi Inari" in transcript or "Kyoto" in transcript
