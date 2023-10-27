from unittest.mock import patch

import pytest

from app.core.settings.app import AppSettings
from app.crud.crud_place import CRUDPlaceFactory
from app.schemas.google_maps_api import DistanceInfo
from app.services.constants import AGGREGATED_ATTR
from app.services.routes_matrix_services import DestinationSummary, RoutesMatrix
from app.tests.utils.places import create_random_place, distance_info_list


def test_update_candidate_addresses(db, settings: AppSettings):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    with patch("app.crud.crud_place.CRUDPlaceFactory.get_instance") as mock_instance:
        mock_instance.return_value = crud_place
        place_has_no_address = [
            create_random_place(
                db,
                crud_place=crud_place,
                place_id="1",
                name="판교역",
                address="fake1",
            ),
            create_random_place(
                db,
                crud_place=crud_place,
                place_id="2",
                name="서울역",
                address="fake2",
            ),
        ]

        destination_with_perfect_address = [
            DistanceInfo(
                origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
                destination_id="1",
                destination="perfect1",
                distance_text="2.2 km",
                distance_value=2186,
                duration_text="22분",
                duration_value=1299,
            ),
            DistanceInfo(
                origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
                destination_id="2",
                destination="perfect2",
                distance_text="2.2 km",
                distance_value=2186,
                duration_text="22분",
                duration_value=1299,
            ),
        ]
        assert place_has_no_address[0].address == "fake1"
        assert place_has_no_address[1].address == "fake2"
        routes_matrix = RoutesMatrix(destination_with_perfect_address)
        routes_matrix.update_candidate_addresses(db, place_has_no_address)

        assert (
            crud_place.get_by_place_id(id=place_has_no_address[0].place_id).address
            == "perfect1"
        )
        assert (
            crud_place.get_by_place_id(id=place_has_no_address[1].place_id).address
            == "perfect2"
        )


def test_sort_destinations_by_aggregated_attr():
    routes_matrix = RoutesMatrix(distance_info_list)
    res = routes_matrix.sort_destinations_by_aggregated_attr(
        AGGREGATED_ATTR.DURATION,
        2,
    )

    assert res == [
        DestinationSummary(
            destination_id="ChIJN1t_tDeuEmsRUsoyG83frY1",
            total_value=distance_info_list[0].duration_value
            + distance_info_list[2].duration_value,
        ),
        DestinationSummary(
            destination_id="ChIJN1t_tDeuEmsRUsoyG83frY2",
            total_value=distance_info_list[1].duration_value
            + distance_info_list[3].duration_value,
        ),
    ]
