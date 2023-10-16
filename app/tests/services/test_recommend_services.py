from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytz
from sqlalchemy.orm import Session

from app.core.settings.app import AppSettings
from app.crud.crud_place import CRUDPlaceFactory
from app.models.place import Place
from app.schemas.google_maps_api import GeocodeResponse
from app.services.constants import PLACETYPE, REDIS_SEARCH_RADIUS
from app.services.recommend_services import CandidateFetcher, Recommender
from app.services.redis_services import RedisServicesFactory
from app.tests.utils.places import create_random_place, user_preferences


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


def test_get_cached_places(db: Session, map_service, normal_user, redis_services):
    redis_services.add_location_to_redis(37.0, 127.0)
    redis_services.cache_nearby_places_response(37.0, 127.0, ["test"])

    map_service.process_nearby_places_results = MagicMock(return_value=["test"])
    candidate_fetcher = CandidateFetcher(db, normal_user, map_service, redis_services)

    places = candidate_fetcher._get_cached_places(37.0, 127.0, REDIS_SEARCH_RADIUS)

    assert places == ["test"]


def test_get_cached_places_no_cache(db: Session, map_service, normal_user):
    redis_services = RedisServicesFactory.create_redis_services()

    candidate_fetcher = CandidateFetcher(db, normal_user, map_service, redis_services)

    places = candidate_fetcher._get_cached_places(37.0, 127.0, REDIS_SEARCH_RADIUS)

    assert places == []


def test_fetch_places_by_coordinates_with_cached(
    db: Session, map_service, normal_user, redis_services
):
    redis_services.add_location_to_redis(37.0, 127.0)
    redis_services.cache_nearby_places_response(37.0, 127.0, ["test"])

    candidate_fetcher = CandidateFetcher(db, normal_user, map_service, redis_services)
    candidate_fetcher._get_cached_places = MagicMock(return_value=["test"])

    places = candidate_fetcher.fetch_places_by_coordinates(37.0, 127.0, PLACETYPE.CAFE)

    assert places == ["test"]


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


def test_recommend_places_many_address(db, map_service, normal_user):
    recommender = Recommender(db, normal_user, map_service, user_preferences)

    recommender.candidate_fetcher = MagicMock()
    recommender.rank_candidates = MagicMock()

    addresses = ["판교역", "서현역"]
    candidates = [MagicMock(spec=Place), MagicMock(spec=Place)]
    recommender.candidate_fetcher.fetch_by_midpoint.return_value = candidates

    ranked_candidates = [MagicMock(spec=Place), MagicMock(spec=Place)]
    recommender.rank_candidates.return_value = ranked_candidates

    result = recommender.recommend_places_by_address(db, addresses)

    assert result == ranked_candidates
    recommender.candidate_fetcher.fetch_by_midpoint.assert_called_once_with(
        addresses, user_preferences.place_type
    )
    recommender.rank_candidates.assert_called_once_with(candidates, addresses=addresses)


def test_recommend_places_one_address(db, map_service, normal_user):
    recommender = Recommender(db, normal_user, map_service, user_preferences)

    recommender.candidate_fetcher = MagicMock()
    recommender.rank_candidates = MagicMock()

    addresses = ["서현역"]
    candidates = [MagicMock(spec=Place), MagicMock(spec=Place)]
    recommender.candidate_fetcher.fetch_by_address.return_value = candidates

    ranked_candidates = [MagicMock(spec=Place)]
    recommender.rank_candidates.return_value = ranked_candidates

    result = recommender.recommend_places_by_address(db, addresses)

    assert result == ranked_candidates
    recommender.candidate_fetcher.fetch_by_address.assert_called_once_with(
        addresses[0], user_preferences.place_type
    )
    recommender.rank_candidates.assert_called_once_with(candidates, addresses=addresses)


def test_compute_recentness_weight_over_7days(
    db, settings: AppSettings, map_service, normal_user
):
    recommender = Recommender(db, normal_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place) for _ in range(1)]
    candidate_dict = candidates[0].model_dump()
    candidate_dict["created_at"] = datetime.now(pytz.utc) - timedelta(days=8)

    weight = recommender._compute_recentness_weight(candidate_dict["created_at"])

    assert weight == 1.0


def test_compute_recentness_weight_under_7days(
    db, settings: AppSettings, map_service, normal_user
):
    recommender = Recommender(db, normal_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place) for _ in range(1)]
    candidate_dict = candidates[0].model_dump()
    candidate_dict["created_at"] = datetime.now(pytz.utc) - timedelta(days=6)

    weight = recommender._compute_recentness_weight(candidate_dict["created_at"])

    assert weight == 1.5


def test_compute_scores_for_candidates(
    db, map_service, settings: AppSettings, normal_user
):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place) for _ in range(3)]

    recommender = Recommender(db, normal_user, map_service, user_preferences)

    scores = recommender._compute_scores_for_candidates(candidates)

    assert len(scores) == 3
    for score in scores:
        assert len(score) == 2


def test_compute_reccomendation_score_just_rating(
    db, map_service, settings: AppSettings, normal_user
):
    recommender = Recommender(db, normal_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place) for _ in range(1)]
    candidates[0].rating = 4.0

    score = recommender.compute_recommendation_score(candidates[0])

    assert score == 4.0


def test_compute_reccomendation_score_with_preferred_types_rating(
    db, map_service, settings: AppSettings
):
    mock_user = MagicMock()
    mock_user.interested_places = []
    mock_user.search_history_relations = []
    mock_user.preferred_types = ["cafe"]
    recommender = Recommender(db, mock_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place) for _ in range(1)]
    candidates[0].place_types = ["cafe", "restaurant"]
    candidates[0].rating = 4.0

    score = recommender.compute_recommendation_score(candidates[0])
    assert score == 6.0


def test_compute_reccomendation_score_with_search_history_relations(
    db, map_service, settings: AppSettings
):
    mock_user = MagicMock()
    mock_user.interested_places = []
    mock_user.search_history_relations = [
        MagicMock(address="판교역", created_at=datetime.now(pytz.utc) - timedelta(days=6)),
        MagicMock(address="서현역", created_at=datetime.now(pytz.utc) - timedelta(days=6)),
    ]
    recommender = Recommender(db, mock_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)
    candidates = [create_random_place(db, crud_place, address="역교판") for _ in range(1)]

    candidates[0].rating = 4.0

    score = recommender.compute_recommendation_score(candidates[0])
    assert score <= 6.0


def test_rank_candidates(db, settings: AppSettings, map_service, normal_user):
    recommender = Recommender(db, normal_user, map_service, user_preferences)
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV)

    candidates = [create_random_place(db, crud_place) for _ in range(2)]

    recommender._generate_routes_matrix = MagicMock(return_value=[[1, 2], [3, 4]])
    recommender._update_routes_matrix_addresses = MagicMock()
    recommender._filter_candidates_by_routes = MagicMock(
        return_value=[candidates[0], candidates[1]]
    )
    recommender._compute_scores_for_candidates = MagicMock(
        return_value=[(candidates[0], 1), (candidates[1], 2)]
    )

    results = recommender.rank_candidates(
        candidates, [candidate.address for candidate in candidates]
    )

    recommender._generate_routes_matrix.assert_called_once_with(
        [candidate.address for candidate in candidates], candidates
    )
    recommender._update_routes_matrix_addresses.assert_called_once_with(
        recommender._generate_routes_matrix.return_value, candidates
    )
    recommender._filter_candidates_by_routes.assert_called_once_with(
        recommender._generate_routes_matrix.return_value, candidates
    )

    recommender._compute_scores_for_candidates.assert_called_once_with(
        recommender._filter_candidates_by_routes.return_value
    )

    assert results == [candidates[1], candidates[0]]
