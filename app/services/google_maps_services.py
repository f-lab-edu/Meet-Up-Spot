from typing import Dict, List

import requests
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core.config import get_app_settings
from app.schemas.google_maps_api import GeocodeResponse
from app.schemas.google_maps_api_log import GoogleMapsApiLogCreate
from app.schemas.location import Location, LocationCreate
from app.schemas.place import AutoCompletedPlace, Place, PlaceCreate

settings = get_app_settings()

STATUS_DETAIL_MAPPING = {
    "ZERO_RESULTS": "찾을 수 없는 주소입니다.",
    "OVER_DAILY_LIMIT": "API 키가 누락되었거나 잘못되었습니다.",
    "OVER_QUERY_LIMIT": "할당량이 초과되었습니다.",
    "REQUEST_DENIED": "요청이 거부되었습니다.",
    "INVALID_REQUEST": "입력값이 누락되었습니다.",
    "UNKNOWN_ERROR": "서버 내부 오류가 발생했습니다.",
}


class GoogleMapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def handle_status(self, status_code, status):
        if status in STATUS_DETAIL_MAPPING:
            raise HTTPException(
                status_code=status_code, detail=STATUS_DETAIL_MAPPING[status]
            )
        else:
            raise HTTPException(status_code=status_code, detail="알 수 없는 상태 코드입니다.")

    def create_or_get_location(self, db, result) -> Location:
        latitude = result["geometry"]["location"]["lat"]
        longitude = result["geometry"]["location"]["lng"]
        compound_code = result["plus_code"]["compound_code"]
        global_code = result["plus_code"]["global_code"]

        existing_location = crud.location.get_by_plus_code(
            db, compound_code=compound_code, global_code=global_code
        )
        return existing_location or crud.location.create(
            db,
            obj_in=LocationCreate(
                latitude=latitude,
                longitude=longitude,
                compound_code=compound_code,
                global_code=global_code,
            ),
        )

    def create_or_get_place(self, db, result, location_id) -> Place:
        place_id = result["place_id"]
        existing_place = crud.place.get_by_place_id(db, id=place_id)

        return existing_place or crud.place.create(
            db,
            obj_in=PlaceCreate(
                place_id=result["place_id"],
                name=result["name"],
                address=result["vicinity"],
                user_ratings_total=result.get("user_ratings_total", 0),
                rating=result.get("rating", 0),
                location_id=location_id,
                place_types=result["types"],
            ),
        )

    def geocode_address(self, address: str) -> GeocodeResponse:
        """
        주소를 Geocoding하여 경도와 위도를 반환하는 Geocoding API 요청
        """
        # Google Maps Geocoding API 엔드포인트 URL
        url = self.base_url

        # API 키와 주소 설정
        api_key = self.api_key
        params = {
            "address": address,
            "key": api_key,
        }

        # Geocoding 요청 보내기
        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(data)
            # 첫 번째 결과의 경도와 위도 추출
            if status == "OK":
                location = data["results"][0]["geometry"]["location"]
                return GeocodeResponse(
                    latitude=location["lat"], longitude=location["lng"]
                )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )

    def reverse_geocode(self, latitude, longitude):
        """
        위도와 경도로 주소를 반환하는 Reverse Geocoding API 요청
        """

        params = {"latlng": f"{latitude},{longitude}", "key": self.api_key}

        response = requests.get(self.base_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")

            if status == "OK":
                return data["results"][0]["formatted_address"]
            else:
                self.handle_status(response.status_code, status)

        else:
            raise HTTPException(
                status_code=status, detail="Geocoding API 요청 중 오류가 발생했습니다."
            )

    def search_nearby_places(
        self,
        db: Session,
        latitude,
        longitude,
        radius=500,
    ) -> List[Place]:
        """
        주변 지역 검색 API 요청
        """
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "cafe|restaurant|bar",
            "key": self.api_key,
        }

        response = requests.get(
            settings.GOOGLE_MAPS_NEARBY_SEARCH_URL, params=params, timeout=5
        )

        crud.google_maps_api_log.create(
            db,
            obj_in=GoogleMapsApiLogCreate(
                user_id=1,
                status_code=response.status_code,
                reason=response.reason,
                request_url=settings.GOOGLE_MAPS_NEARBY_SEARCH_URL,
                payload=params,
                print_result=response.text,
            ),
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "OK":
                results = data["results"][:5]
                return [
                    self.create_or_get_place(
                        db, result, self.create_or_get_location(db, result).id
                    )
                    for result in results
                ]
            else:
                self.handle_status(response.status_code, status)

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )

    # TODO: 위치 기반이 되야 할거 같음. 현재 위치를 기반으로 주변 장소를 검색하고, 그 장소들을 기반으로 추천을 해야할듯
    def auto_complete_place(self, text: str) -> List[AutoCompletedPlace]:
        """
        장소 자동 완성 API 요청
        """
        params = {
            "input": text,
            "language": "ko",
            "key": self.api_key,
        }
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/autocomplete/json",
            params=params,
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "OK":
                return [
                    AutoCompletedPlace(
                        address=prediction["description"],
                        main_address=prediction["structured_formatting"]["main_text"],
                        secondary_address=prediction["structured_formatting"][
                            "secondary_text"
                        ],
                        place_id=prediction["place_id"],
                    )
                    for prediction in data["predictions"]
                ]
            else:
                self.handle_status(response.status_code, status)

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )

    def get_place_detail(self, place_id: str):
        """
        장소 상세 정보 API 요청
        """
        params = {
            "place_id": place_id,
            "key": self.api_key,
        }
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params=params,
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            if status == "OK":
                return data["result"]
            else:
                self.handle_status(response.status_code, status)

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )
