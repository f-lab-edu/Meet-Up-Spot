from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.models.user import User
from app.schemas.google_maps_api import GeocodeResponse, UserPreferences
from app.schemas.place import Place
from app.services.constants import PLACETYPE, Radius
from app.services.filters_services import DistanceInfoFilter
from app.services.map_services import MapServices
from app.services.routes_matrix_services import RoutesMatrix

from .midpoint_services import calculate_midpoint_from_addresses, harversine_distance


class CandidateFetcher:
    def __init__(self, db: Session, user: User, map_services: MapServices):
        self.map_services = map_services
        self.user = user
        self.db = db

    def decide_radius(self, geocoded_addresses: List[GeocodeResponse]):
        maximum_distance = 0
        length = len(geocoded_addresses)
        for i in range(length):
            for j in range(i + 1, length):
                distance = harversine_distance(
                    geocoded_addresses[i], geocoded_addresses[j]
                )
                if distance > maximum_distance:
                    maximum_distance = distance

            if maximum_distance >= Radius.THIRD_RADIUS.value * 2:
                return Radius.THIRD_RADIUS.value
        return maximum_distance // 2

    def fetch_by_address(self, address: str, place_type: PLACETYPE) -> List[Place]:
        geocoded_address = self.map_services.get_lat_lng_from_address(
            self.db, self.user, address
        )
        if not geocoded_address:
            raise Exception("Failed to geocode address.")

        return self.map_services.get_nearby_places(
            self.db,
            self.user,
            geocoded_address.latitude,
            geocoded_address.longitude,
            place_type=place_type,
        )

    def fetch_by_midpoint(
        self, addresses: List[str], place_type: PLACETYPE
    ) -> List[Place]:
        geocoded_addresses = self.map_services.get_geocoded_addresses(
            self.db, self.user, addresses
        )

        midpoint = calculate_midpoint_from_addresses(
            geocoded_addresses=geocoded_addresses,
        )
        if not midpoint:
            raise Exception("Failed to calculate midpoint.")

        return self.map_services.get_nearby_places(
            self.db,
            self.user,
            midpoint.latitude,
            midpoint.longitude,
            place_type=place_type,
            radius=self.decide_radius(geocoded_addresses),
        )


class Recommender:
    def __init__(
        self,
        db: Session,
        user: User,
        map_services: MapServices,
        user_preferences: UserPreferences,
    ):
        self.db = db
        self.user = user
        self.map_services = map_services
        self.candidate_fetcher = CandidateFetcher(db, user, map_services)
        self.user_preferences: UserPreferences = user_preferences

    def recommend_places(
        self,
        db: Session,
        addresses: List[str],
    ) -> List[Place]:
        if len(addresses) == 1:
            candidates = self.candidate_fetcher.fetch_by_address(
                addresses[0],
                self.user_preferences.place_type,
            )
        else:
            candidates = self.candidate_fetcher.fetch_by_midpoint(
                addresses, self.user_preferences.place_type
            )
        return self.rank_candidates(candidates, addresses=addresses)

    # TODO:추가적인 랭킹 또는 필터링 로직을 적용
    def rank_candidates(
        self,
        candidates: List[Place],
        addresses: List[str],
    ) -> List[Place]:
        routes_matrix = RoutesMatrix(
            self.map_services.get_distance_matrix_for_places(
                self.db,
                self.user,
                origins=addresses,
                destinations=[candidate.place_id for candidate in candidates],
            )
        )

        # NOTE: 약간 어색하지만 중간에 candidate랑 get_distance_matrix_for_places애서 찾아온 주소가 일관성이 없어서 여기서 수정해줌
        routes_matrix.update_candidate_addresses(self.db, candidates)

        filtered_cadidates = DistanceInfoFilter(
            routes_matrix, self.user_preferences
        ).apply(candidates)

        return filtered_cadidates
