from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TravelContent(BaseModel):
    """Unified internal representation for all media and text travel sources."""

    source_type: str = Field(
        ..., json_schema_extra={"example": "social_post"}, description="Source type: image, video, text, social_post"
    )
    caption: Optional[str] = Field(
        None,
        json_schema_extra={"example": "Exploring Shibuya crossing in Tokyo!"},
        description="Text caption or post content",
    )
    frames: List[bytes] = Field(default_factory=list, description="Visual keyframe images")
    ocr_text: Optional[str] = Field(None, description="Extracted OCR text overlay")
    speech_text: Optional[str] = Field(None, description="Audio speech transcript")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata key-value attributes (URL, author, platform)"
    )


class UniversalExtractionRequest(BaseModel):
    """Public API request payload for universal multi-source extraction."""

    source_type: str = Field(
        ...,
        json_schema_extra={"example": "text"},
        description="Type of source: 'text', 'image_url', 'video_url', 'raw'",
    )
    content: str = Field(
        ...,
        json_schema_extra={
            "example": "Spent the weekend exploring cafes around Kyoto and visited Fushimi Inari Shrine."
        },
        description="Text content, social media post, or media URL",
    )
    context: Optional[str] = Field(
        None, json_schema_extra={"example": "Japan trip"}, description="Optional location context or region hint"
    )
