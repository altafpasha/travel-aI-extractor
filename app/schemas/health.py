from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response schema for system health check."""
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    app_name: str = Field(..., json_schema_extra={"example": "Travel AI Extractor"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
