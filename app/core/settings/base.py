from enum import Enum

from pydantic_settings import BaseSettings


class AppEnvTypes(str, Enum):
    prod: str = "production"
    dev: str = "development"
    test: str = "test"


class BaseAppSettings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.dev

    class Config:
        env_file = ".env"
