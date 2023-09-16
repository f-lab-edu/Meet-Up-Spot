from typing import List

from sqlalchemy.orm import Session

from app.schemas.google_maps_api import GeocodeResponse
from app.schemas.place import Place

from .google_maps_services import GoogleMapsService
from .midpoint_services import calculate_midpoint_from_addresses


# TODO: 추천 알고리즘 구현 (기본적으로 place rating 기반, 그리고 카페를 우선순위로)
class Recommender:
    def __init__(self):
        self.maps_service = GoogleMapsService()

    def recommend_places(
        self, db: Session, addresses: List[str], radius: int = 1500
    ) -> List[Place]:
        try:
            if len(addresses) == 1:
                geocoded_address = self.maps_service.geocode_address(addresses[0])
                places = self.maps_service.search_nearby_places(
                    db, geocoded_address.latitude, geocoded_address.longitude, radius
                )
            else:
                midpoint: GeocodeResponse = calculate_midpoint_from_addresses(addresses)

                if midpoint:
                    places: List[Place] = self.maps_service.search_nearby_places(
                        db, midpoint.latitude, midpoint.longitude, radius
                    )
                else:
                    raise Exception("Failed to calculate midpoint.")
            return places
        except Exception as e:
            print(f"Error while recommending places: {str(e)}")
            return []
