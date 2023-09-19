import logging
from functools import wraps
from typing import Dict, List

import googlemaps
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
from app.services.constants import PlaceType

settings = get_app_settings()

STATUS_DETAIL_MAPPING = {
    "ZERO_RESULTS": "찾을 수 없는 주소입니다.",
    "OVER_DAILY_LIMIT": "API 키가 누락되었거나 잘못되었습니다.",
    "OVER_QUERY_LIMIT": "할당량이 초과되었습니다.",
    "REQUEST_DENIED": "요청이 거부되었습니다.",
    "INVALID_REQUEST": "입력값이 누락되었습니다.",
    "UNKNOWN_ERROR": "서버 내부 오류가 발생했습니다.",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZeroResultException(Exception):
    pass


class CustomException(Exception):
    pass


class MapAdapter:
    def __init__(self, client=None, db=None):
        self.client = client
        self.db = db

    def format_place_id(self, place_id):
        return f"place_id:{place_id}"

    def geocode_address(self, address):
        result = self.client.geocode(address)
        return result

    def reverse_geocode(self, latitude, longitude):
        return self.client.reverse_geocode((latitude, longitude))

    def search_nearby_places(
        self,
        latitude,
        longitude,
        radius=1000,
        language="ko",
        place_type=PlaceType.CAFE.value,
    ) -> List[dict]:
        # Using the places_nearby method from the official library
        return self.client.places_nearby(
            location=(latitude, longitude),
            radius=radius,
            language=language,
            type=place_type,
        )

    def auto_complete_place(self, text: str, language="ko") -> List[dict]:
        return self.client.places_autocomplete(text, language=language)

    def get_place_detail(self, place_id: str):
        return self.client.place(place_id=place_id)

    def calculate_distance_matrix(
        self,
        origins,
        destination,
        mode="transit",
        language="ko",
    ):
        # Using the distance_matrix method from the official library
        print(mode)
        try:
            matrix = self.client.distance_matrix(
                origins=origins,
                destinations=self.format_place_id(destination),
                mode=mode,
                language=language,
            )
            print(matrix)

            distances = []
            for row in matrix["rows"]:
                for element in row["elements"]:
                    if element["status"] == "ZERO_RESULTS":
                        raise HTTPException(
                            status_code=400,
                            detail="No route found for one or more origin-destination pairs.",
                        )

                    distance = element["distance"]["text"]
                    duration = element["duration"]["text"]

                    distances.append((distance, duration))

            return distances
        except Exception as e:
            raise CustomException(e)


class MapServices:
    def __init__(self, map_client=None):
        if map_client is None:
            map_client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        self.map_adapter = MapAdapter(map_client)

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

    def get_lat_lng_from_address(self, address: str) -> GeocodeResponse:
        results = self.map_adapter.geocode_address(address)

        if not results:
            raise ZeroResultException("No geocoding results found")

        location = results[0]["geometry"]["location"]
        return GeocodeResponse(latitude=location["lat"], longitude=location["lng"])

    def get_address_from_lat_lng(self, latitude: float, longitude: float) -> str:
        result = self.map_adapter.reverse_geocode(latitude, longitude)
        if not result:
            raise ZeroResultException("No reverse geocoding results found")

        return result[0]["formatted_address"]

    def search_nearby_places(
        self,
        db: Session,
        latitude,
        longitude,
        radius=1000,
        language="ko",
        place_type=PlaceType.CAFE.value,
    ) -> List[Place]:
        """
        주변 지역 검색 API 요청
        """
        response = self.map_adapter.search_nearby_places(
            latitude, longitude, radius=radius, language="ko"
        )
        results = response["results"]
        if not results:
            logging.warning("No nearby places found for the given coordinates.")
            raise ZeroResultException("No nearby places found")

        places = []
        for result in results[:5]:
            try:
                location = self.create_or_get_location(db, result)
                place = self.create_or_get_place(db, result, location.id)
                places.append(place)
            except Exception as e:
                logging.error(f"Failed to process result {result}. Error: {e}")
                continue
        return places

    def get_complete_addresses(self, addresses: List[str]) -> List[str]:
        complete_addresses = []
        for address in addresses:
            complete_addresses.append(self.auto_complete_place(address)[0].address)
        return complete_addresses

    # TODO: 위치 기반이 되야 할거 같음. 현재 위치를 기반으로 주변 장소를 검색하고, 그 장소들을 기반으로 추천을 해야할듯
    def auto_complete_place(self, text: str) -> List[AutoCompletedPlace]:
        results = self.map_adapter.auto_complete_place(text)
        return [
            AutoCompletedPlace(
                address=prediction["description"],
                main_address=prediction["structured_formatting"]["main_text"],
                secondary_address=prediction["structured_formatting"]["secondary_text"],
                place_id=prediction["place_id"],
            )
            for prediction in results
        ]

    def get_distance_matrix_for_places(
        self,
        origins,
        destination,
        mode="driving",
        language="ko",
    ):
        """
        origins: list of origins
        destination: single destination
        mode: "driving", "walking", or "transit"
        language: language in which to return results, default is "ko"
        """

        # Ensure the selected mode is valid
        if mode not in ["driving", "walking", "transit", "bicycling"]:
            raise ValueError(
                "Invalid mode selected. Choose between 'driving', 'walking', or 'transit'."
            )
        print("mode", mode)

        params = {
            "origins": origins,
            "destination": destination,
            "mode": mode,
            "language": language,
        }

        distances = self.map_adapter.calculate_distance_matrix(**params)
        print("distances", distances)
        if not distances:
            raise ZeroResultException("No distance matrix results found")

        return distances
