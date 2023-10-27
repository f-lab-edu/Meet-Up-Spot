from app.schemas.google_maps_api import GeocodeResponse
from app.services.midpoint_services import (
    calculate_midpoint_arithmetic,
    calculate_midpoint_from_addresses,
    calculate_midpoint_harvarsine,
    harversine_distance,
)


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
