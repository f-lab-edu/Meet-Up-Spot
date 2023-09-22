from unittest.mock import MagicMock, patch

import pytest

from app import crud
from app.core.settings.app import AppSettings
from app.models.google_maps_api_log import GoogleMapsApiLog
from app.services.map_services import CustomException, MapServices


def test_get_lat_lng_from_address_logs_on_exception(
    db, map_service: MapServices, settings: AppSettings, monkeypatch
):
    def mock_geocode(*args, **kwargs):
        raise CustomException("test")

    monkeypatch.setattr(map_service.map_adapter, "geocode_address", mock_geocode)

    mock_log_create = MagicMock()
    monkeypatch.setattr("app.crud.google_maps_api_log.create", mock_log_create)

    test_user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    test_address = "invalid_address"

    with pytest.raises(CustomException):
        map_service.get_lat_lng_from_address(db, test_user, test_address)

        mock_log_create.assert_called_once()


def test_search_nearby_places_logs_on_exception(
    db, map_service: MapServices, settings: AppSettings, monkeypatch
):
    def mock_nearby(*args, **kwargs):
        raise CustomException("test")

    monkeypatch.setattr(map_service.map_adapter, "search_nearby_places", mock_nearby)
    mock_log_create = MagicMock()
    monkeypatch.setattr("app.crud.google_maps_api_log.create", mock_log_create)

    test_user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)

    with pytest.raises(CustomException):
        map_service.search_nearby_places(
            db, test_user, latitude=37.0, longitude=127.0, radius=1000
        )

        mock_log_create.assert_called_once()


def test_read_auto_completed_places(
    client, superuser_token_headers, db, settings: AppSettings
):
    with pytest.raises(CustomException):  # 예외 유형을 적절한 것으로 바꾸세요.
        client.get(
            f"{settings.API_V1_STR}/places/completed-places/ㅁㄴ",
            headers=superuser_token_headers,
        )

        log_entry = (
            db.query(GoogleMapsApiLog).order_by(GoogleMapsApiLog.id.desc()).first()
        )
        assert log_entry is not None
        assert (
            log_entry.request_url
            == "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        )


def test_get_distance_matrix(
    client, superuser_token_headers, db, settings: AppSettings
):
    origins = ["Address 1", "Address 2"]
    destination_id = "ChIJu3CCEgJYezURGV8SqFwsMJo"

    with pytest.raises(CustomException):
        client.post(
            f"{settings.API_V1_STR}/places/{destination_id}/get-travel-info",
            headers=superuser_token_headers,
            json=origins,
        )

        log_entry = (
            db.query(GoogleMapsApiLog).order_by(GoogleMapsApiLog.id.desc()).first()
        )
        assert log_entry is not None
        assert (
            log_entry.request_url
            == "http://testserver/api/v1/places/ChIJu3CCEgJYezURGV8SqFwsMJo/get-travel-info"
        )
