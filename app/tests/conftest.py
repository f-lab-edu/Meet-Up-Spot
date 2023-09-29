from typing import Dict, Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.base import Base
from app.db.session import SessionLocal
from app.services.map_services import MapServices
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from main import app

app_settings = get_app_settings()

engine = create_engine(app_settings.DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

global_db = TestingSessionLocal()


# pylint: disable=no-member
@pytest.fixture(scope="session")
def db() -> Generator:
    db = SessionLocal()
    yield db
    for table in reversed(Base.metadata.sorted_tables):
        if (
            table == Base.metadata.tables["user"]
            or table == Base.metadata.tables["google_maps_api_logs"]
        ):
            continue
        db.execute(table.delete())
    db.commit()
    db.close()


def get_global_db_override():
    return global_db


@pytest.fixture(scope="session")
def client() -> Generator:
    app.dependency_overrides[get_db] = get_global_db_override
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def settings() -> Generator:
    yield get_app_settings()


@pytest.fixture(scope="session")
def superuser_token_headers(
    client: TestClient, settings: AppSettings
) -> Dict[str, str]:
    return get_superuser_token_headers(client, settings)


@pytest.fixture(scope="session")
def normal_user_token_headers(
    client: TestClient, db: Session, settings: AppSettings
) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client,
        email=settings.EMAIL_TEST_USER,
        db=db,
    )


@pytest.fixture
def map_service():
    with patch("app.services.map_services.googlemaps.Client") as MockClient:
        mock_client = MockClient()
        service = MapServices(mock_client)
        yield service


@pytest.fixture
def normal_user(db: Session, settings: AppSettings):
    from app.tests.utils.user import create_random_user

    return create_random_user(db)
