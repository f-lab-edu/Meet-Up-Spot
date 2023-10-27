from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api.deps import get_db, get_map_services
from app.core.config import get_app_settings
from app.schemas.google_maps_api import DistanceInfo, UserPreferences
from app.schemas.location import LocationBase
from app.schemas.msg import Msg
from app.schemas.place import AutoCompletedPlace, Place
from app.services import user_service
from app.services.constants import AGGREGATED_ATTR, PLACETYPE, TravelMode
from app.services.map_services import MapServices, ZeroResultException
from app.services.recommend_services import Recommender

router = APIRouter()

settings = get_app_settings()


@router.post("/recommendations/by-address", response_model=List[Place])
def recommend_places_based_on_requested_address(
    addresses: List[str],
    place_type: PLACETYPE = PLACETYPE.CAFE,
    max_results: int = 5,
    filter_condition: AGGREGATED_ATTR = AGGREGATED_ATTR.DISTANCE,
    current_user: models.User = Depends(user_service.get_current_active_user),
    db: Session = Depends(get_db),
    map_services: MapServices = Depends(get_map_services),
):
    """
    request meeting places
    """
    try:
        recommend_services = Recommender(
            db,
            current_user,
            map_services,
            UserPreferences(
                place_type=place_type,
                return_count=max_results,
                filter_condition=filter_condition,
            ),
        )
        complete_addresses = map_services.get_complete_addresses(
            db, current_user, addresses
        )

        crud.user.add_search_history(db, current_user, complete_addresses)
        results: List[Place] = recommend_services.recommend_places_by_address(
            db,
            complete_addresses,
        )

        return results
    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=HTTPStatus.NO_CONTENT, detail=error_msg)
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"An error occurred: {error}"
            )


@router.post("/recommendations/by-location", response_model=List[Place])
def recommend_places_based_on_current_location(
    location: LocationBase,
    place_type: PLACETYPE = PLACETYPE.CAFE,
    max_results: int = 5,
    filter_condition: AGGREGATED_ATTR = AGGREGATED_ATTR.DISTANCE,
    current_user: models.User = Depends(user_service.get_current_active_user),
    db: Session = Depends(get_db),
    map_services: MapServices = Depends(get_map_services),
):
    """
    Recommend places based on user's current location.
    """
    try:
        user_service.update_user_location_if_needed(db, current_user, location)

        # NOTE: 여기서는 유저 위치 기반으로 일반적인 추천을 하기 떄문에 검색에는 추가하지 않음
        recommend_services = Recommender(
            db,
            current_user,
            map_services,
            UserPreferences(
                place_type=place_type,
                return_count=max_results,
                filter_condition=filter_condition,
            ),
        )

        results: List[Place] = recommend_services.recommend_places_by_location(
            db,
            location.latitude,
            location.longitude,
        )

        return results
    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=HTTPStatus.NO_CONTENT, detail=error_msg)
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"An error occurred: {error}"
            )


@router.get("/{place_id}", response_model=Place)
def read_place_by_id(
    place_id: str,
    current_user: models.User = Depends(user_service.get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve place.
    """
    place = crud.place.get_by_place_id(db, id=place_id)

    if not place:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Place not found")

    return place


# TODO: 유저 place 타입 기반으로 필터링 하거나 엔드포인트 추가
@router.get("/", response_model=List[Place])
def read_places(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    Retrieve places.
    """

    places = crud.place.get_multi(db)
    if not places:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Places not found")
    return places


@router.post("/{place_id}/mark", response_model=Msg)
def mark_interest(
    place_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    mark up place.

    """
    place = crud.place.get_by_place_id(db, id=place_id)
    if not place:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Place not found")
    if crud.user.has_interest(db, current_user, place):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Already marked place"
        )

    crud.user.mark_interest(db, current_user, place)
    return {"msg": "Place successfully marked"}


@router.delete("/{place_id}/unmark", response_model=Msg)
def unmark_interest(
    place_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    unmark place.

    """
    place = crud.place.get_by_place_id(db, id=place_id)

    if not place:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Place not found")
    if not crud.user.has_interest(db, current_user, place):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Not marked place"
        )

    crud.user.unmark_interest(db, current_user, place)
    return {"msg": "Place successfully unmarked"}


@router.get("/completed-places/{address}", response_model=List[AutoCompletedPlace])
def read_auto_completed_places(
    address: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
    map_services: MapServices = Depends(get_map_services),
):
    """
    retrieve some auto completed places
    """
    try:
        places = map_services.get_auto_completed_place(db, current_user, address)

        return places
    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=HTTPStatus.NO_CONTENT, detail=error_msg)
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"An error occurred: {error}"
            )


@router.post("/{destination_id}/get-travel-info", response_model=List[DistanceInfo])
def get_distance_matrix(
    origins: List[str],
    destination_id: str,
    mode: TravelMode = TravelMode.TRANSIT,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
    map_services: MapServices = Depends(get_map_services),
) -> List[DistanceInfo]:
    try:
        distances = map_services.get_distance_matrix_for_places(
            db, current_user, origins, destination_id, mode, is_place_id=True
        )

        return distances

    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=HTTPStatus.NO_CONTENT, detail=error_msg)
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"An error occurred: {error}"
            )
