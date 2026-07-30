from fastapi import APIRouter

from app.api.v1.cache import router as cache_router
from app.api.v1.extract import router as extract_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(extract_router)
api_v1_router.include_router(cache_router)
api_v1_router.include_router(jobs_router)
