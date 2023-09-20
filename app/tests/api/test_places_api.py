from typing import Dict
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings.app import AppSettings
from app.tests.utils.places import (
    auto_completed_place_schema,
    mock_geocode_response,
    mock_place_obj,
    places_list,
    test_address,
)


def test_request_places(client: TestClient, db: Session, settings: AppSettings):
    with patch(
        "app.api.endpoints.places.map_services.get_complete_addresses",
        return_value=[test_address],
    ) as mock_get_complete, patch(
        "app.api.endpoints.places.recommend_services.recommend_places",
        return_value=[mock_place_obj],
    ) as mock_recommend:
        response = client.post(
            f"{settings.API_V1_STR}/places/request-places/", json=[test_address]
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_get_complete.assert_called_once()
        mock_recommend.assert_called_once()


def test_request_midpoint(client: TestClient, db: Session, settings: AppSettings):
    with patch(
        "app.api.endpoints.places.map_services.get_complete_addresses",
        return_value=[test_address],
    ) as mock_get_complete, patch(
        "app.api.endpoints.places.recommend_services.recommend_places",
        return_value=mock_geocode_response,
    ) as mock_recommend:
        response = client.post(
            f"{settings.API_V1_STR}/places/request-midpoint/", json=[test_address]
        )
        assert response.status_code == 200
        mock_get_complete.assert_called_once()
        mock_recommend.assert_called_once()


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
    client: TestClient, db: Session, settings: AppSettings
):
    with patch(
        "app.services.map_services.MapServices.auto_complete_place",
        return_value=[auto_completed_place_schema],
    ) as mock_auto_complete:
        response = client.get(
            f"{settings.API_V1_STR}/places/completed-places/{test_address}"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_auto_complete.assert_called_once_with(test_address)


def test_get_distance_matrix(client: TestClient, db: Session, settings: AppSettings):
    test_destination_id = "sample_destination_id"
    origins = ["origin_1", "origin_2"]
    mock_distances = [["origin_1", "10km"], ["origin_2", "15km"]]

    with patch(
        "app.services.map_services.MapServices.get_distance_matrix_for_places",
        return_value=mock_distances,
    ) as mock_distance_matrix:
        response = client.post(
            f"{settings.API_V1_STR}/places/{test_destination_id}/get-travel-info",
            json=origins,
        )

        assert response.status_code == 200
        assert response.json() == mock_distances
        mock_distance_matrix.assert_called_once_with(
            origins, test_destination_id, "driving", "ko"
        )
