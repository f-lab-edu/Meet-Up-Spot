from fastapi import APIRouter

from app.core.config import get_app_settings
from app.core.settings.base import AppEnvTypes

from .endpoints import goolge_maps_api_test as api_test
from .endpoints import login, place, user

settings = get_app_settings()

api_router = APIRouter()
api_router.include_router(
    place.router, prefix="/places", tags=["google_maps"]
)  # geocode 라우터 추가
api_router.include_router(login.router, tags=["login"])
api_router.include_router(user.router, prefix="/users", tags=["user"])
api_router.include_router(user.admin_router, prefix="/admin", tags=["admin"])
if settings.APP_ENV == AppEnvTypes.dev:
    api_router.include_router(api_test.test_router, prefix="/test", tags=["test"])
