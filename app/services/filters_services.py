from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from app.models.place import Place
from app.schemas.google_maps_api import DistanceInfo, UserPreferences
from app.services.constants import AGGREGATED_ATTR, PLACETYPE
from app.services.routes_matrix_services import RoutesMatrix

T = TypeVar("T")


class Filter(ABC, Generic[T]):
    @abstractmethod
    def apply(self, items: List[T]) -> List[T]:
        pass


class FilterChain:
    def __init__(self, filters: List[Filter]):
        self.filters = filters

    def apply(self, items: List[T]) -> List[T]:
        result = items
        for filter in self.filters:
            result = filter.apply(result)
        return result


class PlaceTypeFilter(Filter):
    def __init__(self, place_type: PLACETYPE):
        self.place_types = PLACETYPE


class DistanceInfoFilter(Filter):
    def __init__(self, routes_matrix: RoutesMatrix, user_preferences: UserPreferences):
        self.routes_matrix = routes_matrix
        self.user_preferences = user_preferences

    def apply(self, candidates: List[Place]) -> List[Place]:
        sorted_destination_distance = (
            self.routes_matrix.sort_destinations_by_aggregated_attr(
                self.user_preferences.filter_condition,
                self.user_preferences.return_count,
            )
        )

        aggregated_destination_ids = {
            result.destination_id for result in sorted_destination_distance
        }

        filtered_candidates = [
            candidate
            for candidate in candidates
            if candidate.place_id in aggregated_destination_ids
        ]

        return filtered_candidates[: self.user_preferences.return_count]
