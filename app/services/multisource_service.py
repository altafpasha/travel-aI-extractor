import httpx
from typing import Optional, Dict, Any
from app.schemas.multisource import TravelContent, UniversalExtractionRequest
from app.core.exceptions import TravelExtractorException
from app.core.logging import logger


class MultiSourceEngine:
    """Engine normalizing disparate travel content sources into unified TravelContent format."""

    @staticmethod
    async def build_travel_content(request: UniversalExtractionRequest) -> TravelContent:
        """
        Converts a UniversalExtractionRequest into a unified TravelContent data model.
        """
        source_type = request.source_type.lower()
        content = request.content.strip()

        if source_type == "text":
            return TravelContent(
                source_type="text",
                caption=content,
                metadata={"context_hint": request.context, "context": request.context}
            )

        elif source_type in ("image_url", "video_url"):
            logger.info(f"Downloading media from URL '{content[:60]}...'")
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(content)
                    if resp.status_code != 200:
                        raise TravelExtractorException(
                            f"Failed to fetch media URL (HTTP {resp.status_code})",
                            status_code=400
                        )

                    media_bytes = resp.content
                    if source_type == "image_url":
                        return TravelContent(
                            source_type="image",
                            frames=[media_bytes],
                            caption=request.context,
                            metadata={"url": content}
                        )
                    else:
                        # video URL
                        return TravelContent(
                            source_type="video",
                            frames=[media_bytes],  # Handled downstream by video processor
                            caption=request.context,
                            metadata={"url": content}
                        )
            except Exception as e:
                logger.error(f"Error fetching media URL '{content}': {str(e)}")
                # Fallback as text if download fails
                return TravelContent(
                    source_type="text",
                    caption=f"{content} {request.context or ''}".strip(),
                    metadata={"error": str(e)}
                )

        else:
            # Fallback raw
            return TravelContent(
                source_type="text",
                caption=content,
                metadata={"context_hint": request.context}
            )
