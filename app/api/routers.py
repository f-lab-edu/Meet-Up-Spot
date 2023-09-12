from fastapi import APIRouter

from .endpoints import login, user

api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(user.admin_router, prefix="/admin", tags=["admin"])
