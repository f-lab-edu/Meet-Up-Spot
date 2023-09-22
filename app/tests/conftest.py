from typing import Dict, Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.base import Base
from app.db.session import SessionLocal
from app.services.map_services import MapServices
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from main import app


# pylint: disable=no-member
@pytest.fixture(scope="module")
def db() -> Generator:
    db = SessionLocal()
    yield db
    for table in reversed(Base.metadata.sorted_tables):
        if table == Base.metadata.tables["user"]:
            continue
        db.execute(table.delete())
    db.commit()
    db.close()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def settings() -> Generator:
    yield get_app_settings()


@pytest.fixture(scope="module")
def superuser_token_headers(
    client: TestClient, settings: AppSettings
) -> Dict[str, str]:
    return get_superuser_token_headers(client, settings)


@pytest.fixture(scope="module")
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
