from unittest.mock import MagicMock

import pytest

from app import crud
from app.schemas.google_maps_api import DistanceInfo
from app.services.map_services import CustomException, MapServices, ZeroResultException
from app.tests.utils.places import (
    mock_geocode_response,
    mock_location,
    mock_place_api_response,
    mock_place_obj,
)


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


def test_get_lat_lng_from_address(map_service: MapServices, db, normal_user):
    map_service.map_adapter.geocode_address = MagicMock(
        return_value=mock_geocode_response
    )

    response = map_service.get_lat_lng_from_address(db, normal_user, "Test Address")

    assert response.latitude == 123.456
    assert response.longitude == 789.101


def test_get_lat_lng_from_address_no_result(map_service: MapServices, db, normal_user):
    map_service.map_adapter.client.geocode = MagicMock(return_value=[])

    with pytest.raises(CustomException):
        map_service.get_lat_lng_from_address(db, normal_user, "Invalid Address")


@pytest.mark.parametrize("db", [MagicMock()])
def test_create_or_get_location_existing(map_service: MapServices, db, normal_user):
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


def test_get_distance_matrix_for_places_one_destination(map_service, db, normal_user):
    distance_info_1 = (
        DistanceInfo(
            origin="origin_1",
            destination="destination_1",
            distance_text="10km",
            distance_value=10000,
            duration_text="20분",
            duration_value=1200,
        ),
    )
    distance_info_2 = (
        DistanceInfo(
            origin="origin_2",
            destination="destination_1",
            distance_text="15km",
            distance_value=15000,
            duration_text="30분",
            duration_value=1800,
        ),
    )

    map_service.map_adapter.calculate_distance_matrix = MagicMock(
        return_value=[distance_info_1, distance_info_2]
    )

    response = map_service.get_distance_matrix_for_places(
        db, normal_user, ["origin_1", "origin_2"], ["destination_1"], "transit"
    )

    assert response == [distance_info_1, distance_info_2]
    map_service.map_adapter.calculate_distance_matrix.assert_called_once()


def test_calculate_distance_matrix(db, normal_user, map_service):
    map_service.map_adapter.client = MagicMock()
    map_service.map_adapter.client.distance_matrix.return_value = {
        "destination_addresses": [
            "대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
            "대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        ],
        "origin_addresses": ["대한민국 경기도 성남시 분당구 성남대로 지하 601 서현", "대한민국 서울특별시 양재역"],
        "rows": [
            {
                "elements": [
                    {
                        "distance": {"text": "2.2 km", "value": 2186},
                        "duration": {"text": "22분", "value": 1299},
                        "status": "OK",
                    },
                    {
                        "distance": {"text": "29.4 km", "value": 29450},
                        "duration": {"text": "53분", "value": 3168},
                        "status": "OK",
                    },
                ]
            },
            {
                "elements": [
                    {
                        "distance": {"text": "12.9 km", "value": 12881},
                        "duration": {"text": "13분", "value": 805},
                        "status": "OK",
                    },
                    {
                        "distance": {"text": "15.5 km", "value": 15475},
                        "duration": {"text": "34분", "value": 2065},
                        "status": "OK",
                    },
                ]
            },
        ],
        "status": "OK",
    }

    response = map_service.map_adapter.calculate_distance_matrix(
        db,
        normal_user,
        origins=["대한민국 경기도 성남시 분당구 성남대로 지하 601 서현", "대한민국 서울특별시 양재역"],
        destinations=[
            "대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
            "대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        ],
        mode="transit",
        language="ko",
    )

    assert response == [
        DistanceInfo(
            origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
            destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
            distance_text="2.2 km",
            distance_value=2186,
            duration_text="22분",
            duration_value=1299,
        ),
        DistanceInfo(
            origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
            destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
            distance_text="29.4 km",
            distance_value=29450,
            duration_text="53분",
            duration_value=3168,
        ),
        DistanceInfo(
            origin="대한민국 서울특별시 양재역",
            destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
            distance_text="12.9 km",
            distance_value=12881,
            duration_text="13분",
            duration_value=805,
        ),
        DistanceInfo(
            origin="대한민국 서울특별시 양재역",
            destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
            distance_text="15.5 km",
            distance_value=15475,
            duration_text="34분",
            duration_value=2065,
        ),
    ]
