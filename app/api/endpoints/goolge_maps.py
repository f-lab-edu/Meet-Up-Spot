from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.google_maps_api import RequestSpotResponse, ReverseGeocodeRequest
from app.services.google_maps_services import GoogleMapsService
from app.services.midpoint_services import calculate_midpoint_from_addresses
from app.services.recommend_services import Recommender

router = APIRouter()

goggle_maps_service = GoogleMapsService()
recommend_service = Recommender()


@router.get(
    "/",
)
async def geocode(address: str):
    """
    주소를 Geocoding하여 경도와 위도를 반환합니다.
    """
    location = goggle_maps_service.geocode_address(address)
    return {"latitude": location["lat"], "longitude": location["lng"]}


@router.get("/reverse_geocode/")
async def reverse_geocode(request_data: ReverseGeocodeRequest):
    """
    위도와 경도로 주소를 반환하는 Reverse Geocoding API 요청
    """
    results = goggle_maps_service.reverse_geocode(
        request_data.latitude, request_data.longitude
    )
    return {"results": results}


@router.get("/calculate_midpoint/")
async def calculate_midpoint_endpoint(request_data: List[str]):
    """
    Geocode한 주소들의 중간 위치를 계산하는 API 엔드포인트
    """
    midpoint = calculate_midpoint_from_addresses(request_data)

    if midpoint:
        return {"midpoint": {"latitude": midpoint[0], "longitude": midpoint[1]}}
    else:
        return {"error": "Failed to calculate midpoint."}


## text 로 찾고 위도/경도로 찾고 둘다 있어야 할듯
@router.get("/search_nearby/")
async def search_nearby_endpoint(latitude: float, longitude: float, radius: int):
    """
    특정 위치 반경 내의 장소를 검색하는 API 엔드포인트
    """
    results = goggle_maps_service.search_nearby_places(latitude, longitude, radius)
    return {"results": results}


@router.post(
    "/request_spot/",
)
async def request_spots(addresses: List[str], db: Session = Depends(get_db)):
    """
    유저에게 주소를 입력받아 만남 장소를 추천하는 API 엔드포인트
    """
    complete_addresses = []
    for address in addresses:
        complete_addresses.append(
            goggle_maps_service.auto_complete_place(address)[0]["description"]
        )

    results = recommend_service.recommend_places(db, complete_addresses)
    return {"results": results}


@router.get("/autocomplete/")
async def autocomplete(address: str):
    """
    주소를 입력받아 자동완성 API 엔드포인트
    """
    results = goggle_maps_service.auto_complete_place(address)
    return {"results": results}
