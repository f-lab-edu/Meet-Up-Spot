import logging
import secrets

from app.core.settings.app import AppSettings


class TestAppSettings(AppSettings):
    debug: bool = True

    title: str = "Test FastAPI example application"

    SECRET_KEY: str = secrets.token_urlsafe(32)

    max_connection_count: int = 5
    min_connection_count: int = 5

    logging_level: int = logging.DEBUG

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6378


settings = TestAppSettings()
