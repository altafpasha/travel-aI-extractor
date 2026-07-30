from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TextExtractionRequest(BaseModel):
    """Request payload for text place extraction."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Raw text, social media caption, or post content",
        json_schema_extra={"example": "Spent the weekend exploring cafes around Kyoto and visited Fushimi Inari Shrine."}
    )
    context: Optional[str] = Field(
        None,
        description="Optional location context hint (e.g. region, city, country)",
        json_schema_extra={"example": "Japan"}
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty or whitespace only.")
        return v.strip()


class ExtractedPlaceRaw(BaseModel):
    """Raw place extracted directly from Gemini before Places API verification."""
    name: str = Field(..., description="Name of the place or landmark")
    city: Optional[str] = Field(None, description="City where the place is located")
    country: Optional[str] = Field(None, description="Country where the place is located")
    category: Optional[str] = Field(None, description="Type/category of place e.g. landmark, restaurant, hotel, cafe")


class PlaceLocation(BaseModel):
    """Enriched, validated place location response model."""
    name: str = Field(..., json_schema_extra={"example": "Fushimi Inari Shrine"})
    city: Optional[str] = Field(None, json_schema_extra={"example": "Kyoto"})
    country: Optional[str] = Field(None, json_schema_extra={"example": "Japan"})
    confidence: int = Field(..., ge=0, le=100, json_schema_extra={"example": 96}, description="Confidence percentage score (0-100)")
    address: Optional[str] = Field(None, json_schema_extra={"example": "68 Fukakusa Yabunouchicho, Fushimi Ward, Kyoto, 612-0882, Japan"})
    latitude: Optional[float] = Field(None, json_schema_extra={"example": 34.9671})
    longitude: Optional[float] = Field(None, json_schema_extra={"example": 135.7727})
    place_id: Optional[str] = Field(None, json_schema_extra={"example": "ChIJ31-1ZkQGAWARf0N5e9..."})
    verified: bool = Field(default=False, description="Whether the location was successfully verified by Google Places API")

    model_config = ConfigDict(from_attributes=True)


class ImageExtractionResponse(BaseModel):
    """Structured response payload returned by POST /extract/image and POST /extract/text."""
    destination: Optional[str] = Field(..., json_schema_extra={"example": "Kyoto"}, description="Primary overall destination or region identified")
    places: List[PlaceLocation] = Field(default_factory=list, description="List of extracted and verified places")
    execution_time_seconds: float = Field(..., description="Processing duration in seconds")

    model_config = ConfigDict(from_attributes=True)


class ExtractionErrorResponse(BaseModel):
    """Error payload returned when extraction fails."""
    error: str
    message: str
