from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.tipsters import router as tipsters_router
from app.api.v1.endpoints.channels import router as channels_router
from app.api.v1.endpoints.videos import router as videos_router
from app.api.v1.endpoints.analyses import router as analyses_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(tipsters_router)
api_router.include_router(channels_router)
api_router.include_router(videos_router)
api_router.include_router(analyses_router)
