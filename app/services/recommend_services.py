import logging
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Tuple

import pytz
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.google_maps_api import GeocodeResponse, UserPreferences
from app.schemas.place import Place
from app.services.constants import PLACETYPE, REDIS_SEARCH_RADIUS, Radius
from app.services.filters_services import DistanceInfoFilter
from app.services.map_services import MapServices
from app.services.redis_services import RedisServicesFactory
from app.services.routes_matrix_services import RoutesMatrix

from .midpoint_services import calculate_midpoint_from_addresses, harversine_distance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandidateFetcher:
    def __init__(
        self, db: Session, user: User, map_services: MapServices, redis_services=None
    ):
        self.map_services = map_services
        self.user = user
        self.db = db
        self.redis_services = (
            RedisServicesFactory.create_redis_services()
            if not redis_services
            else redis_services
        )

    def decide_api_radius(self, geocoded_addresses: List[GeocodeResponse]):
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

    def _get_cached_places(self, latitude, longitude, redis_search_radius):
        places = []
        geohashes_in_radius = self.redis_services.find_geohashes_in_radius(
            latitude, longitude, redis_search_radius
        )

        cached_api_responses = self.redis_services.get_cached_nearby_places_responses(
            geohashes_in_radius
        )

        if cached_api_responses:
            logger.info("Found cached nearby places responses.")
            for cached_api_response in cached_api_responses:
                places.extend(
                    self.map_services.process_nearby_places_results(
                        self.db, self.user, cached_api_response
                    )
                )
        return places

    def fetch_places_by_coordinates(
        self,
        latitude,
        longitude,
        place_type,
        api_search_radius=Radius.FIRST_RADIUS.value,
    ):
        places = self._get_cached_places(latitude, longitude, REDIS_SEARCH_RADIUS)

        if not places:
            places = self.map_services.get_nearby_places(
                self.db,
                self.user,
                latitude,
                longitude,
                place_type=place_type,
                radius=api_search_radius,
            )

        return places

    def fetch_by_address(self, address: str, place_type: PLACETYPE) -> List[Place]:
        geocoded_address = self.map_services.get_lat_lng_from_address(
            self.db, self.user, address
        )
        if not geocoded_address:
            raise Exception("Failed to geocode address.")

        return self.fetch_places_by_coordinates(
            geocoded_address.latitude,
            geocoded_address.longitude,
            place_type,
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

        return self.fetch_places_by_coordinates(
            midpoint.latitude,
            midpoint.longitude,
            place_type,
            self.decide_api_radius(geocoded_addresses),
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
        self.recommendation_weights = {
            "interest": 5.0,
            "search": 1.0,
            "type": 2.0,
            "rating": 1.0,
            "recentness": lambda x: 1.5 if x <= 7 else 1.0,
        }

    def _generate_routes_matrix(
        self, addresses: List[str], candidates: List[Place]
    ) -> RoutesMatrix:
        return RoutesMatrix(
            self.map_services.get_distance_matrix_for_places(
                self.db,
                self.user,
                origins=addresses,
                destinations=[candidate.place_id for candidate in candidates],
            )
        )

    # NOTE: 약간 어색하지만 중간에 candidate랑 get_distance_matrix_for_places애서 찾아온 주소가 일관성이 없어서 여기서 수정해줌
    def _update_routes_matrix_addresses(
        self, routes_matrix: RoutesMatrix, candidates: List[Place]
    ):
        routes_matrix.update_candidate_addresses(self.db, candidates)

    def _filter_candidates_by_routes(
        self, routes_matrix: RoutesMatrix, candidates: List[Place]
    ) -> List[Place]:
        return DistanceInfoFilter(routes_matrix, self.user_preferences).apply(
            candidates
        )

    def _compute_scores_for_candidates(
        self, candidates: List[Place]
    ) -> List[Tuple[Place, float]]:
        return [
            (candidate, self.compute_recommendation_score(candidate))
            for candidate in candidates
        ]

    def _compute_string_similarity(self, s1: str, s2: str) -> float:
        return round(SequenceMatcher(None, s1, s2).ratio(), 2)

    def _compute_recentness_weight(self, searched_date: datetime) -> float:
        cur_utc_time = datetime.now(pytz.utc)
        assert cur_utc_time > searched_date
        days_since_searched = (cur_utc_time - searched_date).days
        # NOTE: 최근 7일 이내에 검색된 장소는 더 높은 가중치를 받음
        return self.recommendation_weights["recentness"](days_since_searched)

    def compute_recommendation_score(self, place: Place):
        score = 0

        if place in self.user.interested_places:
            score += self.recommendation_weights["interest"]

        for history in self.user.search_history_relations:
            similarity = self._compute_string_similarity(history.address, place.address)
            recentness = self._compute_recentness_weight(history.created_at)
            score += self.recommendation_weights["search"] * similarity * recentness

        type_similarity = len(set(place.place_types) & set(self.user.preferred_types))

        score += self.recommendation_weights["type"] * type_similarity

        score += self.recommendation_weights["rating"] * place.rating

        return score

    def recommend_places_by_address(
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

    def recommend_places_by_location(
        self, db: Session, latitude: float, longitude: float
    ) -> List[Place]:
        candidates = self.candidate_fetcher.fetch_places_by_coordinates(
            latitude, longitude, self.user_preferences.place_type
        )
        return self.rank_candidates(candidates, addresses=[f"{latitude},{longitude}"])

    def rank_candidates(
        self,
        candidates: List[Place],
        addresses: List[str],
    ) -> List[Place]:
        routes_matrix = self._generate_routes_matrix(addresses, candidates)

        self._update_routes_matrix_addresses(routes_matrix, candidates)

        filtered_candidates = self._filter_candidates_by_routes(
            routes_matrix, candidates
        )
        scored_places = self._compute_scores_for_candidates(filtered_candidates)

        scored_places.sort(key=lambda x: x[1], reverse=True)

        print(scored_places)

        return [socre_place[0] for socre_place in scored_places]
