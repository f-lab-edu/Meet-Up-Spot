from functools import lru_cache
from typing import Dict, Type

from app.core.settings.app import AppSettings
from app.core.settings.base import AppEnvTypes
from app.core.settings.development import settings as DevAppSettings
from app.core.settings.production import settings as ProdAppSettings
from app.core.settings.test import settings as TestAppSettingss

environments: Dict[AppEnvTypes, Type[AppSettings]] = {
    AppEnvTypes.dev: DevAppSettings,
    AppEnvTypes.prod: ProdAppSettings,
    AppEnvTypes.test: TestAppSettingss,
}


@lru_cache
def get_app_settings() -> AppSettings:
    app_env: AppSettings = AppSettings().app_env
    config = environments[app_env]
    return config
