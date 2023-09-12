from fastapi import APIRouter

from .endpoints import goolge_maps, login, user

api_router = APIRouter()
api_router.include_router(
    goolge_maps.router, prefix="/google_maps", tags=["google_maps"]
)  # geocode 라우터 추가
api_router.include_router(login.router, tags=["login"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(user.admin_router, prefix="/admin", tags=["admin"])
