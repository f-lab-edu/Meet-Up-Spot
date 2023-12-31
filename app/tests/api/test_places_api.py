from typing import Dict
from unittest.mock import ANY, MagicMock, create_autospec, patch

from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.settings.app import AppSettings
from app.services.constants import PLACETYPE
from app.services.recommend_services import Recommender
from app.tests.utils.places import (
    auto_completed_place_schema,
    distance_info_list,
    mock_place_obj,
    places_list,
    test_address,
)


def test_recommend_places_based_on_requested_address(
    client: TestClient,
    settings: AppSettings,
    normal_user_token_headers,
):
    mock_recommender = create_autospec(Recommender)
    mock_recommender.recommend_places_by_address.return_value = [mock_place_obj]
    with patch("app.api.endpoints.places.Recommender", return_value=mock_recommender):
        response = client.post(
            f"{settings.API_V1_STR}/places/recommendations/by-address",
            json=[test_address],
            headers=normal_user_token_headers,
            params={"place_type": PLACETYPE.CAFE.value, "max_results": 5},
        )

        assert response.status_code == 200
        assert response.json() == [mock_place_obj.model_dump()]

        mock_recommender.recommend_places_by_address.assert_called_once()


def test_recommend_places_based_on_current_location_with_latest_location(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers,
):
    current_user = crud.user.get_by_email(
        db,
        email=settings.EMAIL_TEST_USER,
    )
    mock_recommender = create_autospec(Recommender)
    mock_recommender.recommend_places_by_location.return_value = [mock_place_obj]

    with patch("app.api.endpoints.places.Recommender", return_value=mock_recommender):
        response = client.post(
            f"{settings.API_V1_STR}/places/recommendations/by-location",
            json={"latitude": 127.0, "longitude": 32.0},
            headers=normal_user_token_headers,
            params={"place_type": PLACETYPE.CAFE.value, "max_results": 5},
        )

        assert response.status_code == 200
        assert response.json() == [mock_place_obj.model_dump()]
        assert current_user.latest_location.latitude == 127.0
        assert current_user.latest_location.longitude == 32.0

        mock_recommender.recommend_places_by_location.assert_called_once()


def test_recommend_places_based_on_current_location_without_latest_location(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers,
):
    mock_recommender = create_autospec(Recommender)
    mock_recommender.recommend_places_by_location.return_value = [mock_place_obj]
    crud.user.add_location_history = MagicMock()
    with patch("app.api.endpoints.places.Recommender", return_value=mock_recommender):
        response = client.post(
            f"{settings.API_V1_STR}/places/recommendations/by-location",
            json={"latitude": 31.0, "longitude": 127.0},
            headers=normal_user_token_headers,
            params={"place_type": PLACETYPE.CAFE.value, "max_results": 5},
        )

        assert response.status_code == 200

        assert response.json() == [mock_place_obj.model_dump()]
        crud.user.add_location_history.assert_called_once()

        mock_recommender.recommend_places_by_location.assert_called_once()


def test_read_place_by_id(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers: Dict[str, str],
):
    test_place_id = mock_place_obj.place_id

    with patch("app.api.deps.get_db", return_value=db), patch(
        "app.crud.place.get_by_place_id", return_value=mock_place_obj
    ) as mock_get_place:
        response = client.get(
            f"{settings.API_V1_STR}/places/{test_place_id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        assert response.json() == mock_place_obj.model_dump()
        mock_get_place.assert_called_once_with(ANY, id=test_place_id)


# This example assumes you have a `test_places_list` function or equivalent to generate multiple mock places
def test_read_places(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers: Dict[str, str],
):
    with patch("app.crud.place.get_multi", return_value=places_list) as mock_get_multi:
        response = client.get(
            f"{settings.API_V1_STR}/places", headers=normal_user_token_headers
        )

        assert response.status_code == 200
        assert len(response.json()) == len(places_list)
        mock_get_multi.assert_called_once()


def test_read_auto_completed_places(
    client: TestClient, settings: AppSettings, normal_user_token_headers
):
    with patch(
        "app.services.map_services.MapServices.get_auto_completed_place",
        return_value=[auto_completed_place_schema],
    ) as mock_auto_complete:
        response = client.get(
            f"{settings.API_V1_STR}/places/completed-places/{test_address}",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_auto_complete.assert_called_once_with(ANY, ANY, test_address, None)


def test_get_distance_matrix(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers,
    normal_user,
):
    test_destination_id = "sample_destination_id"
    origins = ["대한민국 경기도 성남시 분당구 성남대로 지하 601 서현", "대한민국 서울특별시 양재역"]

    with patch(
        "app.services.map_services.MapServices.get_distance_matrix_for_places",
        return_value=distance_info_list,
    ) as mock_distance_matrix:
        response = client.post(
            f"{settings.API_V1_STR}/places/{test_destination_id}/get-travel-info",
            json=origins,
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        assert response.json() == jsonable_encoder(distance_info_list)
        mock_distance_matrix.assert_called_once()


def test_mark_interest(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers: Dict[str, str],
):
    test_place_id = mock_place_obj.place_id

    with patch("app.api.deps.get_db", return_value=db), patch(
        "app.crud.place.get_by_place_id", return_value=mock_place_obj
    ) as mock_get_place, patch(
        "app.crud.user.has_interest", return_value=False
    ) as mock_has_interest, patch(
        "app.crud.user.mark_interest"
    ) as mock_mark_interest:
        response = client.post(
            f"{settings.API_V1_STR}/places/{test_place_id}/mark",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        assert response.json() == {"msg": "Place successfully marked"}
        mock_get_place.assert_called_once_with(ANY, id=test_place_id)
        mock_has_interest.assert_called_once_with(ANY, ANY, mock_place_obj)
        mock_mark_interest.assert_called_once_with(ANY, ANY, mock_place_obj)


def test_unmark_interest(
    client: TestClient,
    db: Session,
    settings: AppSettings,
    normal_user_token_headers: Dict[str, str],
):
    test_place_id = mock_place_obj.place_id

    with patch("app.api.deps.get_db", return_value=db), patch(
        "app.crud.place.get_by_place_id", return_value=mock_place_obj
    ) as mock_get_place, patch(
        "app.crud.user.has_interest", return_value=True
    ) as mock_has_interest, patch(
        "app.crud.user.unmark_interest"
    ) as mock_unmark_interest:
        response = client.delete(
            f"{settings.API_V1_STR}/places/{test_place_id}/unmark",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        assert response.json() == {"msg": "Place successfully unmarked"}
        mock_get_place.assert_called_once_with(ANY, id=test_place_id)
        mock_has_interest.assert_called_once_with(ANY, ANY, mock_place_obj)
        mock_unmark_interest.assert_called_once_with(ANY, ANY, mock_place_obj)
