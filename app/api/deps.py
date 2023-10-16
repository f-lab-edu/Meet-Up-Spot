from typing import Generator

import redis
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_app_settings
from app.db.session import SessionLocal
from app.services.map_services import MapServices, MapServicesFactory
from app.services.redis_services import RedisServicesFactory

settings = get_app_settings()

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_redis_services() -> Generator:
    try:
        redis_service = RedisServicesFactory.create_redis_services()
        yield redis_service
    finally:
        # RedisServices 인스턴스는 연결을 직접 관리하지 않으므로 정리할 필요가 없음 내부에서 redis-py 가 알아서 관리함
        pass


def get_map_services() -> MapServices:
    return MapServicesFactory.create_map_services()
