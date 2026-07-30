from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import TravelExtractorException, travel_extractor_exception_handler
from app.core.logging import logger
from app.database.connection import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event handler."""
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    await init_db()
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


def create_application() -> FastAPI:
    """Factory function to build and configure FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Production-grade AI engine for extracting structured travel places from images and screenshots.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    app.add_exception_handler(TravelExtractorException, travel_extractor_exception_handler)

    # Register API Routers
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", response_class=PlainTextResponse, summary="Root endpoint")
    async def root() -> str:
        return "Travel AI Extractor Running"

    return app


app = create_application()
