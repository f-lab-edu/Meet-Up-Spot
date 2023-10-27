from app.schemas.google_maps_api import UserPreferences
from app.services.constants import AGGREGATED_ATTR, PLACETYPE
from app.services.filters_services import DistanceInfoFilter
from app.services.routes_matrix_services import RoutesMatrix
from app.tests.utils.places import (
    distance_info_list,
    places_list_related_to_distance_info,
)


def test_distance_info_filter_apply():
    routes_matrix = RoutesMatrix(distance_info_list)
    user_preferences = UserPreferences(
        place_type=PLACETYPE.CAFE,
        filter_condition=AGGREGATED_ATTR.DISTANCE,
        return_count=1,
    )
    filtered_candidates = DistanceInfoFilter(routes_matrix, user_preferences).apply(
        places_list_related_to_distance_info
    )

    assert len(filtered_candidates) == 1
    assert filtered_candidates[0].name == "판교역"
