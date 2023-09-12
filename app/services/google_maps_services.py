from typing import Dict, List

import requests
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core.config import get_app_settings
from app.schemas.google_maps_api import GeocodeResponse
from app.schemas.google_maps_api_log import GoogleMapsApiLogCreate

settings = get_app_settings()


class GoogleMapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

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
            match status:
                case "OK":
                    location = data["results"][0]["geometry"]["location"]
                    return GeocodeResponse(
                        latitude=location["lat"], longitude=location["lng"]
                    )
                case "ZERO_RESULTS":
                    raise HTTPException(
                        status_code=response.status_code, detail="찾을 수 없는 주소입니다."
                    )
                case "OVER_DAILY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="API 키가 누락되었거나 잘못되었습니다.",
                    )
                case "OVER_QUERY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code, detail="할당량이 초과되었습니다."
                    )
                case "REQUEST_DENIED":
                    raise HTTPException(
                        status_code=response.status_code, detail="요청이 거부되었습니다."
                    )
                case "INVALID_REQUEST":
                    raise HTTPException(
                        status_code=response.status_code, detail="입력값이 누락되었습니다."
                    )
                case "UNKNOWN_ERROR":
                    raise HTTPException(
                        status_code=response.status_code, detail="서버 내부 오류가 발생했습니다."
                    )
                case _:
                    raise HTTPException(
                        status_code=response.status_code, detail="알 수 없는 상태 코드입니다."
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

            match status:
                case "OK":
                    return data
                case "ZERO_RESULTS":
                    raise HTTPException(
                        status_code=response.status_code, detail="찾을 수 없는 주소입니다."
                    )
                case "OVER_QUERY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code, detail="할당량이 초과되었습니다."
                    )
                case "REQUEST_DENIED":
                    raise HTTPException(
                        status_code=response.status_code, detail="요청이 거부되었습니다."
                    )
                case "INVALID_REQUEST":
                    raise HTTPException(
                        status_code=response.status_code, detail="입력값이 누락되었습니다."
                    )
                case "UNKNOWN_ERROR":
                    raise HTTPException(
                        status_code=response.status_code, detail="서버 내부 오류가 발생했습니다."
                    )
                case _:
                    raise HTTPException(
                        status_code=response.status_code, detail="알 수 없는 상태 코드입니다."
                    )

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
    ):
        """
        주변 지역 검색 API 요청
        """
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": "point_of_interest | cafe | restaurant",
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
            # 여기에는  받아온 데이터 처리하는 로직을 넣어야 한다.
            # location = Location.create
            # place = Place.create
            # 일단은 이떄만 저장 하자
            match status:
                case "OK":
                    return data["results"]
                case "ZERO_RESULTS":
                    raise HTTPException(
                        status_code=response.status_code, detail="찾을 수 없는 주소입니다."
                    )
                case "OVER_DAILY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="API 키가 누락되었거나 잘못되었습니다.",
                    )
                case "OVER_QUERY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code, detail="할당량이 초과되었습니다."
                    )
                case "REQUEST_DENIED":
                    raise HTTPException(
                        status_code=response.status_code, detail="요청이 거부되었습니다."
                    )
                case "INVALID_REQUEST":
                    raise HTTPException(
                        status_code=response.status_code, detail="입력값이 누락되었습니다."
                    )
                case "UNKNOWN_ERROR":
                    raise HTTPException(
                        status_code=response.status_code, detail="서버 내부 오류가 발생했습니다."
                    )
                case _:
                    raise HTTPException(
                        status_code=response.status_code, detail="알 수 없는 상태 코드입니다."
                    )

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )

    def search_nearby_places_by_text(self, text: str, radius=1500):
        pass

    def auto_complete_place(self, text: str):
        """
        장소 자동 완성 API 요청
        """
        params = {
            "input": text,
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
            match status:
                case "OK":
                    return data["predictions"]
                case "ZERO_RESULTS":
                    raise HTTPException(
                        status_code=response.status_code, detail="찾을 수 없는 주소입니다."
                    )
                case "OVER_DAILY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="API 키가 누락되었거나 잘못되었습니다.",
                    )
                case "OVER_QUERY_LIMIT":
                    raise HTTPException(
                        status_code=response.status_code, detail="할당량이 초과되었습니다."
                    )
                case "REQUEST_DENIED":
                    raise HTTPException(
                        status_code=response.status_code, detail="요청이 거부되었습니다."
                    )
                case "INVALID_REQUEST":
                    raise HTTPException(
                        status_code=response.status_code, detail="입력값이 누락되었습니다."
                    )
                case "UNKNOWN_ERROR":
                    raise HTTPException(
                        status_code=response.status_code, detail="서버 내부 오류가 발생했습니다."
                    )
                case _:
                    raise HTTPException(
                        status_code=response.status_code, detail="알 수 없는 상태 코드입니다."
                    )

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="Geocoding API 요청 중 오류가 발생했습니다.",
            )
