import logging

from pydantic import PostgresDsn, SecretStr

from app.core.settings.app import AppSettings


class TestAppSettings(AppSettings):
    debug: bool = True

    title: str = "Test FastAPI example application"

    SECRET_KEY: SecretStr = SecretStr("test_secret")

    DATABASE_URL: PostgresDsn
    max_connection_count: int = 5
    min_connection_count: int = 5

    logging_level: int = logging.DEBUG


settings = TestAppSettings()
