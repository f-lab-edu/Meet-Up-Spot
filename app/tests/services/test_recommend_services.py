# mock 필요한 부분, 예를 들면 MapServices를 mock 하려면
from typing import List
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.place import Place
from app.schemas.google_maps_api import DistanceInfo, GeocodeResponse
from app.services.constants import PLACETYPE
from app.services.recommend_services import Recommender
from app.tests.utils.places import mock_place_type_obj, user_preferences


def test_candidate_fetcher_fetch_by_address(
    db: Session,
    map_service,
    normal_user,
):
    # MapServices의 mock 생성
    map_service = MagicMock()
    map_service.get_lat_lng_from_address.return_value = GeocodeResponse(
        latitude=37.0, longitude=127.0
    )
    map_service.get_nearby_places.return_value = []

    recommender = Recommender(db, normal_user, map_service, user_preferences)
    results = recommender.candidate_fetcher.fetch_by_address("판교역", PLACETYPE.CAFE)

    assert results == []


def test_candidate_fetcher_fetch_by_midpoint(db: Session, map_service, normal_user):
    map_service = MagicMock()
    map_service.get_geocoded_addresses.return_value = [
        GeocodeResponse(latitude=37.0, longitude=127.0),
        GeocodeResponse(latitude=38.0, longitude=128.0),
    ]

    map_service.get_nearby_places.return_value = []

    recommender = Recommender(db, normal_user, map_service, user_preferences)
    results = recommender.candidate_fetcher.fetch_by_midpoint(
        ["판교역", "양재역"], PLACETYPE.CAFE
    )

    assert results == []


def test_recommend_places(db, map_service, normal_user):
    recommender = Recommender(db, normal_user, map_service, user_preferences)

    recommender.candidate_fetcher = MagicMock()
    recommender.rank_candidates = MagicMock()

    addresses = ["123 Main St", "456 Elm St"]
    candidates = [MagicMock(spec=Place), MagicMock(spec=Place)]
    recommender.candidate_fetcher.fetch_by_midpoint.return_value = candidates

    ranked_candidates = [MagicMock(spec=Place), MagicMock(spec=Place)]
    recommender.rank_candidates.return_value = ranked_candidates

    result = recommender.recommend_places(db, addresses)

    assert result == ranked_candidates
    recommender.candidate_fetcher.fetch_by_midpoint.assert_called_once_with(
        addresses, user_preferences.place_type
    )
    recommender.rank_candidates.assert_called_once_with(candidates, addresses=addresses)


def test_filter_candidates_by_distance_and_duration(
    db: Session,
    normal_user,
    map_service,
):
    distance_matrix = [
        DistanceInfo(
            origin="Address 5",
            destination="Address 1",
            destination_id="1",
            distance_text="1km",
            distance_value=100,
            duration_text="10분",
            duration_value=100,
        ),
        DistanceInfo(
            origin="Address 5",
            destination="Address 2",
            destination_id="2",
            distance_text="2km",
            distance_value=200,
            duration_text="20분",
            duration_value=200,
        ),
        DistanceInfo(
            origin="Address 5",
            destination="Address 3",
            destination_id="3",
            distance_text="1km",
            distance_value=300,
            duration_text="10분",
            duration_value=300,
        ),
        DistanceInfo(
            origin="Address 6",
            destination="Address 1",
            destination_id="1",
            distance_text="1km",
            distance_value=100,
            duration_text="10분",
            duration_value=100,
        ),
        DistanceInfo(
            origin="Address 6",
            destination="Address 2",
            destination_id="2",
            distance_text="2km",
            distance_value=200,
            duration_text="20분",
            duration_value=200,
        ),
        DistanceInfo(
            origin="Address 6",
            destination="Address 3",
            destination_id="3",
            distance_text="1km",
            distance_value=300,
            duration_text="10분",
            duration_value=300,
        ),
    ]
    candidates = [
        Place(
            place_id="1",
            name="Place 1",
            address="Address 1",
            rating=4.5,
            place_types=[mock_place_type_obj],
        ),
        Place(
            place_id="2",
            name="Place 2",
            address="Address 2",
            rating=4.0,
            place_types=[mock_place_type_obj],
        ),
        Place(
            place_id="3",
            name="Place 3",
            address="Address 3",
            rating=3.5,
            place_types=[mock_place_type_obj],
        ),
    ]
    recommender = Recommender(db, normal_user, map_service, user_preferences)

    result: List[Place] = recommender.filter_candidates_by_distance_and_duration(
        distance_matrix, candidates
    )

    assert len(result) is 2
    assert any(place.place_id == "1" for place in result)
    assert any(place.place_id == "2" for place in result)
    assert not any(place.place_id == "3" for place in result)


def test_rank_candidates_different_destination_id_place_id(
    db, normal_user, map_service
):
    candidates = [
        Place(place_id="B", name="Place B", address="Address B"),
        Place(place_id="C", name="Place C", address="Address C"),
        Place(place_id="D", name="Place D", address="Address D"),
        Place(place_id="E", name="Place E", address="Address E"),
    ]
    addresses = ["Address A", "Address B", "Address C"]
    recommender = Recommender(db, normal_user, map_service, user_preferences)
    distance_matrix = [
        DistanceInfo(
            origin="Address A",
            destination_id="2",
            destination="Address B",
            distance_text="1 km",
            distance_value=1000,
            duration_text="10 mins",
            duration_value=600,
        ),
        DistanceInfo(
            origin="Address A",
            destination_id="2",
            destination="Address C",
            distance_text="2 km",
            distance_value=2000,
            duration_text="20 mins",
            duration_value=1200,
        ),
        DistanceInfo(
            origin="Address A",
            destination_id="4",
            destination="Address D",
            distance_text="3 km",
            distance_value=3000,
            duration_text="30 mins",
            duration_value=1800,
        ),
    ]

    recommender.map_services.get_distance_matrix_for_places = MagicMock()
    recommender.map_services.get_distance_matrix_for_places.return_value = (
        distance_matrix
    )
    with patch(
        "app.services.recommend_services.Recommender.filter_candidates_by_distance_and_duration"
    ) as mock_filter:
        mock_filter.return_value = [
            Place(place_id="B", name="Place B", address="Address B"),
            Place(place_id="C", name="Place C", address="Address C"),
        ]

        result = recommender.rank_candidates(candidates, addresses)
        assert len(result) == 2
        assert result[0].place_id == "B"
        assert result[1].place_id == "C"
        mock_filter.assert_called_once_with(distance_matrix, candidates)
