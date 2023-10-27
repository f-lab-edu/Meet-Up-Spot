import math
from typing import List

from haversine import haversine

from app.schemas.google_maps_api import GeocodeResponse


def calculate_midpoint(locations: List[GeocodeResponse]) -> GeocodeResponse:
    """
    주어진 위치들의 중간 위치를 계산합니다.

    :param locations: 각 위치의 (latitude, longitude) 튜플 리스트
    :return: 중간 위치의 (latitude, longitude) 튜플
    """

    mid_lat, mid_lon = locations[0].latitude, locations[0].longitude
    for next_location in locations[1:]:
        lat1, lon1 = mid_lat, mid_lon
        lat2, lon2 = next_location.latitude, next_location.longitude
        geocoded_midpoint = calculate_midpoint_harvarsine(lat1, lon1, lat2, lon2)

    return geocoded_midpoint


# 산술 평규를 이용한 여러 지점의 중간 지점 계산
def calculate_midpoint_arithmetic(locations: List[GeocodeResponse]) -> GeocodeResponse:
    # 위도와 경도의 평균을 계산
    mid_lat = sum(location.latitude for location in locations) / len(locations)
    mid_lon = sum(location.longitude for location in locations) / len(locations)

    return GeocodeResponse(latitude=mid_lat, longitude=mid_lon)


def calculate_midpoint_harvarsine(lat1, lon1, lat2, lon2) -> GeocodeResponse:
    # 위도와 경도를 라디안 단위로 변환

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # 중간 지점 계산
    Bx = math.cos(lat2) * math.cos(lon2 - lon1)
    By = math.cos(lat2) * math.sin(lon2 - lon1)

    mid_lat = math.atan2(
        math.sin(lat1) + math.sin(lat2), math.sqrt((math.cos(lat1) + Bx) ** 2 + By**2)
    )
    mid_lon = lon1 + math.atan2(By, math.cos(lat1) + Bx)

    # 결과를 도 단위로 변환하여 반환
    mid_lat = math.degrees(mid_lat)
    mid_lon = math.degrees(mid_lon)

    return GeocodeResponse(latitude=mid_lat, longitude=mid_lon)


def harversine_distance(coord1: GeocodeResponse, coord2: GeocodeResponse, unit="m"):
    return haversine(
        (coord1.latitude, coord1.longitude),
        (coord2.latitude, coord2.longitude),
        unit=unit,
    )


def calculate_midpoint_from_addresses(
    geocoded_addresses: List[GeocodeResponse],
) -> GeocodeResponse:
    """
    Geocode한 주소들의 중간 위치를 계산합니다.
    """

    return calculate_midpoint_arithmetic(geocoded_addresses)
