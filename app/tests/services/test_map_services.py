from unittest.mock import MagicMock

import pytest

from app import crud
from app.services.map_services import MapServices, ZeroResultException
from app.tests.utils.places import (
    mock_geocode_response,
    mock_location,
    mock_place_api_response,
    mock_place_obj,
)


def test_get_lat_lng_from_address(map_service: MapServices):
    map_service.map_adapter.geocode_address = MagicMock(
        return_value=mock_geocode_response
    )

    response = map_service.get_lat_lng_from_address("Test Address")

    assert response.latitude == 123.456
    assert response.longitude == 789.101


def test_get_lat_lng_from_address_no_result(map_service: MapServices):
    map_service.map_adapter.geocode_address = MagicMock(return_value=[])

    with pytest.raises(ZeroResultException):
        map_service.get_lat_lng_from_address("Invalid Address")


@pytest.mark.parametrize("db", [MagicMock()])
def test_create_or_get_location_existing(map_service: MapServices, db):
    db.query().filter().first.return_value = mock_location

    result = map_service.create_or_get_location(db, mock_geocode_response[0])

    assert result == mock_location


@pytest.mark.parametrize("db", [MagicMock()])
def test_create_or_get_location_new(map_service: MapServices, db):
    db.query().filter().first.return_value = None
    crud.location.create = MagicMock(return_value=mock_location)

    result = map_service.create_or_get_location(db, mock_geocode_response[0])

    assert result == mock_location
    crud.location.create.assert_called()  # 생성 메서드가 호출되었는지 확인


@pytest.mark.parametrize("db", [MagicMock()])
def test_create_or_get_place_existing(map_service: MapServices, db):
    db.query().filter().first.return_value = mock_place_obj

    result = map_service.create_or_get_place(
        db, mock_place_api_response, mock_location.id
    )
    db.query().filter().first.assert_called_once()
    assert result == mock_place_obj


@pytest.mark.parametrize("db", [MagicMock()])
def test_create_or_get_place_new(map_service: MapServices, db):
    db.query().filter().first.return_value = None
    crud.place.create = MagicMock(return_value=mock_place_obj)

    result = map_service.create_or_get_place(
        db, mock_place_api_response, mock_location.id
    )

    assert result == mock_place_obj
    db.query().filter().first.assert_called_once()
    crud.place.create.assert_called()
