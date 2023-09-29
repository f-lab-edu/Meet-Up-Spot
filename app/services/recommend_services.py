import logging
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.models.user import User
from app.schemas.google_maps_api import DistanceInfo, GeocodeResponse, UserPreferences
from app.schemas.place import Place
from app.services.constants import AGGREGATED_ATTR, PLACETYPE, Radius
from app.services.map_services import MapServices

from .midpoint_services import (
    DestinationSummary,
    calculate_midpoint_from_addresses,
    harversine_distance,
    sort_destinations_by_aggregated_attr,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        print(maximum_distance)
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

    def update_candidate_addresses(
        self, distance_matrix: List[DistanceInfo], candidates: List[Place]
    ):
        """
        Update the address of the candidate.

        :param db: Database session
        :param distance_matrix: The distance matrix results.
        :param candidates: The list of candidates to update.
        """
        candidates_dict = {candidate.place_id: candidate for candidate in candidates}
        for matrix in distance_matrix:
            candidate = candidates_dict.get(matrix.destination_id)
            if candidate and matrix.destination != candidate.address:
                logger.info(
                    f"Updating address: {matrix.destination} != {candidate.address}"
                )
                updated_data = {"address": matrix.destination}
                crud.place.update(self.db, db_obj=candidate, obj_in=updated_data)

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
            # return candidates

    def filter_candidates_by_distance_and_duration(
        self,
        distance_matrix: List[DistanceInfo],
        candidates: List[Place],
    ) -> List[Place]:
        """
        거리와 시간으로 후보 장소들을 필터링합니다.
        """
        min_distance_candidates: List[
            DestinationSummary
        ] = sort_destinations_by_aggregated_attr(
            distance_matrix,
            AGGREGATED_ATTR.DISTANCE,
            self.user_preferences.return_count,
        )
        min_duration_candidates: List[
            DestinationSummary
        ] = sort_destinations_by_aggregated_attr(
            distance_matrix,
            AGGREGATED_ATTR.DURATION,
            self.user_preferences.return_count,
        )

        aggregated_destination_ids = {
            result.destination_id
            for result in min_distance_candidates + min_duration_candidates
        }

        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate.place_id in aggregated_destination_ids
        ]

        # 경로 거리,시간 필터링에서 같은 결과 나올수 있어서 중복 제거
        return list(set(filtered_candidates))[: self.user_preferences.return_count]

    # TODO:추가적인 랭킹 또는 필터링 로직을 적용
    def rank_candidates(
        self,
        candidates: List[Place],
        addresses: List[str],
    ) -> List[Place]:
        distance_matrix: DistanceInfo = (
            self.map_services.get_distance_matrix_for_places(
                self.db,
                self.user,
                origins=addresses,
                destinations=[candidate.place_id for candidate in candidates],
            )
        )

        # NOTE: 약간 어색하지만 중간에 candidate랑 get_distance_matrix_for_places애서 찾아온 주소가 일관성이 없어서 여기서 수정해줌
        self.update_candidate_addresses(distance_matrix, candidates)

        filtered_cadidates = self.filter_candidates_by_distance_and_duration(
            distance_matrix, candidates
        )

        return filtered_cadidates
