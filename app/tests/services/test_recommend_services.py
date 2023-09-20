# mock 필요한 부분, 예를 들면 MapServices를 mock 하려면
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.google_maps_api import GeocodeResponse
from app.services.recommend_services import Recommender


def test_recommender_search_places_by_address(db: Session):
    # MapServices의 mock 생성
    map_services = MagicMock()
    map_services.get_lat_lng_from_address.return_value = GeocodeResponse(
        latitude=37.0, longitude=127.0
    )
    map_services.search_nearby_places.return_value = []

    recommender = Recommender(map_services)
    results = recommender.search_places_by_address(db, "판교역", 1000)

    assert results == []


def test_recommender_search_places_by_midpoint(db: Session):
    map_services = MagicMock()
    map_services.get_lat_lng_from_address.return_value = GeocodeResponse(
        latitude=37.0, longitude=127.0
    )
    map_services.search_nearby_places.return_value = []

    recommender = Recommender(map_services)
    results = recommender.search_places_by_midpoint(db, ["판교역", "양재역"], 1000)

    assert results == []
