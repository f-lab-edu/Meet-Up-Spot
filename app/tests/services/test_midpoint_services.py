# mock 필요한 부분, 예를 들면 MapServices를 mock 하려면
from unittest.mock import MagicMock

from app.schemas.google_maps_api import GeocodeResponse
from app.services.midpoint_services import (
    calculate_midpoint_arithmetic,
    calculate_midpoint_from_addresses,
    calculate_midpoint_harvarsine,
)
from app.services.recommend_services import Recommender


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
    map_services = MagicMock()
    map_services.get_address_from_lat_lng.side_effect = [
        GeocodeResponse(latitude=37.0, longitude=127.0),
        GeocodeResponse(latitude=38.0, longitude=128.0),
    ]

    midpoint = calculate_midpoint_from_addresses(map_services, ["address1", "address2"])

    assert midpoint.latitude == 37.5
    assert midpoint.longitude == 127.5
