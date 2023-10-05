# mock 필요한 부분, 예를 들면 MapServices를 mock 하려면
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.place import Place
from app.schemas.google_maps_api import GeocodeResponse
from app.services.constants import PLACETYPE
from app.services.recommend_services import Recommender
from app.tests.utils.places import user_preferences


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
