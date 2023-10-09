from unittest.mock import MagicMock

import pytest

from app import crud
from app.core.settings.app import AppSettings
from app.crud.crud_location import CRUDLocationFactory
from app.crud.crud_place import CRUDPlaceFactory
from app.schemas.google_maps_api import DistanceInfo
from app.services.constants import TravelMode
from app.services.map_services import MapServices, ZeroResultException
from app.tests.utils.places import (
    create_random_location,
    create_random_place,
    distance_info_list_no_id,
    mock_geocode_response,
    mock_location,
)


def test_create_or_get_locations_all_existing(
    map_service: MapServices, db, settings: AppSettings
):
    crud_location = CRUDLocationFactory.get_instance(settings.APP_ENV)
    map_service._create_new_locations_from_result = MagicMock()
    map_service._extract_lat_lngs_from_results = MagicMock()

    for i in range(3):
        create_random_location(db, crud_location, latitude=i + 1, longitude=i + 1)

    map_service._extract_lat_lngs_from_results.return_value = [
        (i + 1, i + 1) for i in range(3)
    ]

    crud.location.get_by_latlng_list = MagicMock(return_value=crud_location.list)

    map_service._create_new_locations_from_result.return_value = []
    result = map_service.create_or_get_locations(db, crud_location.locations)

    assert len(result) == 3
    assert len(crud_location.locations) == 3


def test_create_or_get_locations_not_existing(
    map_service: MapServices, db, settings: AppSettings
):
    crud_location = CRUDLocationFactory.get_instance(settings.APP_ENV)
    map_service._create_new_locations_from_result = MagicMock()
    map_service._extract_lat_lngs_from_results = MagicMock()

    for i in range(3):
        create_random_location(db, crud_location, latitude=i + 1, longitude=i + 1)

    map_service._extract_lat_lngs_from_results.return_value = [
        (i + 1, i + 1) for i in range(3)
    ]

    crud.location.get_by_latlng_list = MagicMock(return_value=crud_location.list)

    new_locations = [
        create_random_location(db, crud_location, latitude=i + 4, longitude=i + 4)
        for i in range(3)
    ]
    map_service._create_new_locations_from_result.return_value = new_locations
    result = map_service.create_or_get_locations(db, crud_location.locations)

    assert len(result) == 6
    assert len(crud_location.locations) == 6


def test_create_or_get_places_all_existing(
    map_service: MapServices,
    db,
    settings: AppSettings,
):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    map_service._create_new_places_from_results = MagicMock()

    crud_place.places = [
        create_random_place(db, crud_place, place_id=str(i), location_id=i)
        for i in range(3)
    ]
    crud.place.get_by_place_ids = MagicMock(return_value=crud_place.list)

    existing_places = [
        create_random_place(db, crud_place, place_id=str(i), location_id=i).model_dump()
        for i in range(3)
    ]

    map_service._create_new_places_from_results.return_value = []
    result = map_service.create_or_get_places(
        db, existing_places, [i for i in range(3)]
    )

    assert len(result) == 3
    assert len(crud_place.places) == 3


def test_create_or_get_places_not_existing(
    map_service: MapServices, db, settings: AppSettings
):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    map_service._create_new_places_from_results = MagicMock()
    crud_place.places = [
        create_random_place(db, crud_place, place_id=str(i), location_id=i)
        for i in range(3)
    ]
    crud.place.get_by_place_ids = MagicMock(return_value=crud_place.list)

    not_existing_places = [
        create_random_place(db, crud_place, place_id=str(i), location_id=i).model_dump()
        for i in range(3, 6)
    ]
    new_places = [
        create_random_place(db, crud_place, place_id=str(i), location_id=i)
        for i in range(3, 6)
    ]
    map_service._create_new_places_from_results.return_value = new_places
    result = map_service.create_or_get_places(
        db, not_existing_places, [i for i in range(3)]
    )

    assert len(result) == 6
    assert len(crud_place.places) == 6


def test_get_lat_lng_from_address(map_service: MapServices, db, normal_user):
    map_service.map_adapter.geocode_address = MagicMock(
        return_value=mock_geocode_response
    )

    response = map_service.get_lat_lng_from_address(db, normal_user, "판교역")
    assert response.latitude == 123.456
    assert response.longitude == 789.101


def test_get_lat_lng_from_address_no_result(map_service: MapServices, db, normal_user):
    map_service.map_adapter.client.geocode = MagicMock(return_value=[])

    with pytest.raises(ZeroResultException):
        map_service.get_lat_lng_from_address(db, normal_user, "test")


def test_get_distance_matrix_for_places_one_destination(map_service, db, normal_user):
    distance_info_1 = (
        DistanceInfo(
            origin="origin_1",
            destination_id="1",
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
            destination_id="1",
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
        mode=TravelMode.TRANSIT,
        language="ko",
        is_place_id=False,
    )

    assert response == distance_info_list_no_id
