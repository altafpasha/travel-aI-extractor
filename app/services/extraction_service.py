import asyncio
import hashlib
import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.database.repository import ExtractionRepository
from app.schemas.extraction import ImageExtractionResponse, PlaceLocation
from app.schemas.multisource import TravelContent
from app.services.cache_service import CacheService
from app.services.gemini_service import GeminiService
from app.services.ocr_service import OCRService
from app.services.places_service import GooglePlacesService
from app.services.speech_service import AudioSpeechService
from app.services.video_service import FFmpegService


class ExtractionService:
    """Orchestrator service executing multi-modal image, text, video, and universal extraction pipelines."""

    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        places_service: Optional[GooglePlacesService] = None,
        ffmpeg_service: Optional[FFmpegService] = None,
        speech_service: Optional[AudioSpeechService] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        self.gemini_service = gemini_service or GeminiService()
        self.places_service = places_service or GooglePlacesService()
        self.ffmpeg_service = ffmpeg_service or FFmpegService()
        self.speech_service = speech_service or AudioSpeechService()
        self.db_session = db_session
        self.cache_service = CacheService(db_session) if db_session else None

    async def process_travel_content(self, content: TravelContent) -> ImageExtractionResponse:
        """
        Processes normalized TravelContent payload through unified extraction engine.
        """
        if content.source_type == "text" or (not content.frames and content.caption):
            return await self.process_text_extraction(
                text=content.caption or "", context=content.metadata.get("context_hint")
            )

        if content.source_type == "image" and content.frames:
            return await self.process_image_extraction(
                image_bytes=content.frames[0], filename=content.metadata.get("filename", "image_source.jpg")
            )

        if content.source_type == "video" and content.frames:
            return await self.process_video_extraction(
                video_bytes=content.frames[0], filename=content.metadata.get("filename", "video_source.mp4")
            )

        # Fallback text
        return await self.process_text_extraction(text=content.caption or "Travel content")

    async def process_image_extraction(
        self, image_bytes: bytes, filename: str, file_hash: Optional[str] = None, mime_type: str = "image/jpeg"
    ) -> ImageExtractionResponse:
        """
        Executes end-to-end image extraction pipeline:
        SHA256 Check -> Smart Cache -> Local OCR Pre-processing -> Gemini Vision -> Google Places Verification -> Cache Save.
        """
        start_time = time.time()
        file_hash = file_hash or hashlib.sha256(image_bytes).hexdigest()

        if self.cache_service:
            cached_data = await self.cache_service.get_cached_extraction(file_hash)
            if cached_data:
                execution_time = round(time.time() - start_time, 3)
                cached_data["execution_time_seconds"] = execution_time
                logger.info(f"Returning CACHED response for image '{filename}' ({execution_time}s)")
                return ImageExtractionResponse(**cached_data)

        logger.info(f"Cache MISS: Executing image extraction pipeline for '{filename}' ({len(image_bytes)} bytes)...")

        ocr_text = OCRService.extract_text_from_image(image_bytes)
        raw_extraction = await self.gemini_service.extract_places_from_image(
            image_bytes=image_bytes, mime_type=mime_type
        )

        return await self._finalize_extraction_pipeline(
            raw_extraction=raw_extraction,
            identifier=filename,
            file_hash=file_hash,
            start_time=start_time,
            text_context=ocr_text,
        )

    async def process_text_extraction(self, text: str, context: Optional[str] = None) -> ImageExtractionResponse:
        """
        Executes end-to-end text extraction pipeline:
        SHA256 Check -> Smart Cache -> Gemini Text AI -> Google Places Verification -> Cache Save.
        """
        start_time = time.time()
        text_hash = hashlib.sha256(f"{text}_{context or ''}".encode("utf-8")).hexdigest()

        if self.cache_service:
            cached_data = await self.cache_service.get_cached_extraction(text_hash)
            if cached_data:
                execution_time = round(time.time() - start_time, 3)
                cached_data["execution_time_seconds"] = execution_time
                logger.info(f"Returning CACHED response for text extraction ({execution_time}s)")
                return ImageExtractionResponse(**cached_data)

        logger.info(f"Cache MISS: Executing text extraction pipeline ({len(text)} chars)...")

        raw_extraction = await self.gemini_service.extract_places_from_text(text=text, context=context)

        return await self._finalize_extraction_pipeline(
            raw_extraction=raw_extraction,
            identifier=f"text_{text_hash[:10]}",
            file_hash=text_hash,
            start_time=start_time,
            text_context=text,
        )

    async def process_video_extraction(
        self, video_bytes: bytes, filename: str, file_hash: Optional[str] = None
    ) -> ImageExtractionResponse:
        """
        Executes end-to-end video extraction pipeline with Smart Cache lookup.
        """
        start_time = time.time()
        file_hash = file_hash or hashlib.sha256(video_bytes).hexdigest()

        if self.cache_service:
            cached_data = await self.cache_service.get_cached_extraction(file_hash)
            if cached_data:
                execution_time = round(time.time() - start_time, 3)
                cached_data["execution_time_seconds"] = execution_time
                logger.info(f"Returning CACHED response for video '{filename}' ({execution_time}s)")
                return ImageExtractionResponse(**cached_data)

        logger.info(
            f"Cache MISS: Executing multi-modal video extraction pipeline for '{filename}' ({len(video_bytes)} bytes)..."
        )

        frames_task = self.ffmpeg_service.extract_keyframes(video_bytes, filename)
        audio_task = self.ffmpeg_service.extract_audio_track(video_bytes, filename)

        frames, audio_bytes = await asyncio.gather(frames_task, audio_task)

        vision_task = self.gemini_service.extract_places_from_frames(frames)
        speech_task = self.speech_service.transcribe_audio_speech(audio_bytes)

        raw_visual_extraction, spoken_transcript = await asyncio.gather(vision_task, speech_task)

        if spoken_transcript:
            logger.info(f"Extracting places from spoken video transcript: '{spoken_transcript}'")
            spoken_places_res = await self.gemini_service.extract_places_from_text(spoken_transcript)

            seen_names = {p.get("name", "").lower() for p in raw_visual_extraction.get("places", [])}
            for spoken_place in spoken_places_res.get("places", []):
                name = spoken_place.get("name", "").strip()
                if name and name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    raw_visual_extraction["places"].append(spoken_place)

        return await self._finalize_extraction_pipeline(
            raw_extraction=raw_visual_extraction,
            identifier=filename,
            file_hash=file_hash,
            start_time=start_time,
            text_context=spoken_transcript,
        )

    async def _finalize_extraction_pipeline(
        self,
        raw_extraction: dict,
        identifier: str,
        file_hash: Optional[str],
        start_time: float,
        text_context: Optional[str] = None,
    ) -> ImageExtractionResponse:
        """Helper to handle Google Places verification, confidence scoring, timing, database audit logging, and Smart Cache saving."""
        destination = raw_extraction.get("destination")
        raw_places = raw_extraction.get("places", [])

        verified_places: List[PlaceLocation] = []
        if raw_places:
            verification_tasks = [
                self.places_service.verify_and_enrich_place(place, text_context=text_context) for place in raw_places
            ]
            verified_places = await asyncio.gather(*verification_tasks)

        execution_time = round(time.time() - start_time, 3)
        logger.info(f"Extraction pipeline completed in {execution_time}s. Extracted {len(verified_places)} places.")

        response_data = ImageExtractionResponse(
            destination=destination, places=verified_places, execution_time_seconds=execution_time
        )

        if self.db_session:
            try:
                repo = ExtractionRepository(self.db_session)
                await repo.log_extraction(
                    file_name=identifier,
                    file_hash=file_hash,
                    destination=destination,
                    places_count=len(verified_places),
                    raw_response=response_data.model_dump(),
                    execution_time_seconds=execution_time,
                )
                if self.cache_service and file_hash:
                    await self.cache_service.save_extraction_cache(
                        file_hash=file_hash, destination=destination, response_dict=response_data.model_dump()
                    )
            except Exception as db_err:
                logger.error(f"Audit log / Cache save failed: {str(db_err)}")

        return response_data
