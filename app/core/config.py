import os
from functools import lru_cache
from importlib import import_module

from app.core.settings.app import AppSettings
from app.core.settings.base import AppEnvTypes

APP_ENV: str = os.environ.get("APP_ENV", AppEnvTypes.prod.value)
settings_module = import_module(f"app.core.settings.{APP_ENV}")


@lru_cache
def get_app_settings() -> AppSettings:
    config = settings_module.settings
    return config
