from typing import List

from sqlalchemy.orm import Session

from app.schemas.place import Place
from app.services.map_services import MapServices

from .midpoint_services import calculate_midpoint_from_addresses


# TODO: 추천 알고리즘 구현 (기본적으로 place rating 기반, 그리고 카페를 우선순위로)
class Recommender:
    def __init__(self, map_services: MapServices):
        self.map_services = map_services

    def search_places_by_address(
        self, db: Session, address: str, radius: int
    ) -> List[Place]:
        geocoded_address = self.map_services.get_lat_lng_from_address(address)
        return self.map_services.search_nearby_places(
            db, geocoded_address.latitude, geocoded_address.longitude, radius
        )

    def search_places_by_midpoint(
        self, db: Session, addresses: List[str], radius: int
    ) -> List[Place]:
        midpoint = calculate_midpoint_from_addresses(
            map_services=self.map_services, addresses=addresses
        )
        if not midpoint:
            raise Exception("Failed to calculate midpoint.")
        return self.map_services.search_nearby_places(
            db, midpoint.latitude, midpoint.longitude, radius
        )

    def recommend_places(
        self, db: Session, addresses: List[str], radius: int = 2000
    ) -> List[Place]:
        try:
            if len(addresses) == 1:
                return self.search_places_by_address(db, addresses[0], radius)
            else:
                return self.search_places_by_midpoint(db, addresses, radius)
        except Exception as e:
            print(f"Error while recommending places: {str(e)}")
            return []
