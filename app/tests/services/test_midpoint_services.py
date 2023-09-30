# mock 필요한 부분, 예를 들면 MapServices를 mock 하려면
from unittest.mock import MagicMock

from app.schemas.google_maps_api import DistanceInfo, GeocodeResponse
from app.services.constants import AGGREGATED_ATTR
from app.services.midpoint_services import (
    DestinationSummary,
    calculate_midpoint_arithmetic,
    calculate_midpoint_from_addresses,
    calculate_midpoint_harvarsine,
    harversine_distance,
    sort_destinations_by_aggregated_attr,
)
from app.tests.utils.places import distance_info_list


def test_calculate_midpoint():
    loc1 = GeocodeResponse(latitude=37.0, longitude=127.0)
    loc2 = GeocodeResponse(latitude=38.0, longitude=128.0)
    midpoint = calculate_midpoint_arithmetic([loc1, loc2])

    assert midpoint.latitude == 37.5
    assert midpoint.longitude == 127.5


def test_calculate_midpoint_arithmetic():
    loc1 = GeocodeResponse(latitude=37.0, longitude=127.0)
    loc2 = GeocodeResponse(latitude=38.0, longitude=128.0)
    midpoint = calculate_midpoint_arithmetic([loc1, loc2])

    assert midpoint.latitude == 37.5
    assert midpoint.longitude == 127.5


def test_calculate_midpoint_harvarsine():
    lat1, lon1 = 37.0, 127.0
    lat2, lon2 = 38.0, 128.0
    midpoint = calculate_midpoint_harvarsine(lat1, lon1, lat2, lon2)

    assert midpoint.latitude == 37.5010536329402
    assert midpoint.longitude == 127.4966517344202


def test_calculate_midpoint_from_addresses():
    geocoded_address = [
        GeocodeResponse(latitude=37.0, longitude=127.0),
        GeocodeResponse(latitude=38.0, longitude=128.0),
    ]

    midpoint = calculate_midpoint_from_addresses(geocoded_address)

    assert midpoint.latitude == 37.5
    assert midpoint.longitude == 127.5


def test_harversine_distance():
    loc1 = GeocodeResponse(latitude=37.0, longitude=127.0)
    loc2 = GeocodeResponse(latitude=38.0, longitude=128.0)
    distance = harversine_distance(loc1, loc2)

    assert int(distance) == 141936


def test_sort_destinations_by_aggregated_attr():
    res = sort_destinations_by_aggregated_attr(
        distance_info_list,
        AGGREGATED_ATTR.DURATION,
        2,
    )

    assert res == [
        DestinationSummary(
            destination_id="ChIJN1t_tDeuEmsRUsoyG83frY1", total_value=2104
        ),
        DestinationSummary(
            destination_id="ChIJN1t_tDeuEmsRUsoyG83frY2", total_value=5233
        ),
    ]
