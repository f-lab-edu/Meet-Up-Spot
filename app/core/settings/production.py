import os
import sys
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, EmailStr

from app.core.settings.app import AppSettings
from app.core.settings.base import AppEnvTypes

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../..")

ret = load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)


class ProdAppSettings(AppSettings):
    APP_ENV: AppEnvTypes = AppEnvTypes.prod

    POSTGRES_SERVER: str = os.environ["POSTGRES_HOST"]
    POSTGRES_USER: str = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD: str = os.environ["POSTGRES_PASSWORD"]
    POSTGRES_HOST: str = os.environ["POSTGRES_HOST"]
    POSTGRES_DB: str = os.environ["POSTGRES_DB"]

    DATABASE_URL: str = os.environ["DATABASE_URL"]

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = os.environ["BACKEND_CORS_ORIGINS"].split(
        ","
    )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = os.environ["SMTP_PORT"]
    SMTP_HOST: Optional[str] = os.environ["SMTP_HOST"]
    SMTP_USER: Optional[str] = os.environ["SMTP_USER"]
    SMTP_PASSWORD: Optional[str] = os.environ["SMTP_PASSWORD"]
    EMAILS_FROM_EMAIL: Optional[EmailStr] = os.environ["EMAILS_FROM_EMAIL"]
    EMAILS_FROM_NAME: Optional[str] = os.environ["EMAILS_FROM_NAME"]

    class Config(AppSettings.Config):
        env_file = "prod.env"


settings = ProdAppSettings()
