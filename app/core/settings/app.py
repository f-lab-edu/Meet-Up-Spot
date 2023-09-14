import os
import secrets
import sys
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from app.core.settings.base import AppEnvTypes, BaseAppSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)


class AppSettings(BaseAppSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = os.environ["BACKEND_CORS_ORIGINS"].split(
        ","
    )

    APP_ENV: AppEnvTypes = os.environ["APP_ENV"]

    @classmethod
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "Meet-up-spot"
    SENTRY_DSN: Optional[HttpUrl] = None

    # @validator("SENTRY_DSN", pre=True)
    # @classmethod
    # def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
    #     if len(v) == 0:
    #         return None
    #     return v

    POSTGRES_SERVER: str = os.environ["POSTGRES_HOST"]
    POSTGRES_USER: str = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD: str = os.environ["POSTGRES_PASSWORD"]
    POSTGRES_HOST: str = os.environ["POSTGRES_HOST"]
    POSTGRES_DB: str = os.environ["POSTGRES_DB"]
    DATABASE_URL: str = os.environ["DATABASE_URL"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(
        cls, v: Optional[str], values: FieldValidationInfo
    ) -> Any:
        if isinstance(v, str):
            return v
        # pylint: disable=no-member
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            user=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = os.environ["SMTP_PORT"]
    SMTP_HOST: Optional[str] = os.environ["SMTP_HOST"]
    SMTP_USER: Optional[str] = os.environ["SMTP_USER"]
    SMTP_PASSWORD: Optional[str] = os.environ["SMTP_PASSWORD"]
    EMAILS_FROM_EMAIL: Optional[EmailStr] = os.environ["EMAILS_FROM_EMAIL"]
    EMAILS_FROM_NAME: Optional[str] = os.environ["EMAILS_FROM_NAME"]

    @field_validator("EMAILS_FROM_NAME", mode="before")
    @classmethod
    def get_project_name(cls, v: Optional[str], values: FieldValidationInfo) -> str:
        if not v:
            return values.data.get("PROJECT_NAME")
        return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"
    EMAILS_ENABLED: bool = False

    @field_validator(
        "EMAILS_ENABLED",
        mode="before",
    )
    @classmethod
    def get_emails_enabled(cls, v: bool, values: FieldValidationInfo) -> bool:
        return bool(
            values.data.get("SMTP_HOST")
            and values.data.get("SMTP_PORT")
            and values.data.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: EmailStr = os.environ["EMAIL_TEST_USER"]
    EMAIL_TEST_USER_PASSWORD: str = os.environ["EMAIL_TEST_USER_PASSWORD"]

    FIRST_SUPERUSER: EmailStr = os.environ["FIRST_SUPERUSER"]
    FIRST_SUPERUSER_PASSWORD: str = os.environ["FIRST_SUPERUSER_PASSWORD"]
    USERS_OPEN_REGISTRATION: bool = False

    GOOGLE_MAPS_API_KEY: str = os.environ["GOOGLE_MAPS_API_KEY"]
    GOOGLE_MAPS_NEARBY_SEARCH_URL: str = os.environ["GOOGLE_MAPS_NEARBY_SEARCH_URL"]

    class Config:
        case_sensitive = True


settings = AppSettings()
