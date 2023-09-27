from typing import List

import googlemaps
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api.deps import get_db
from app.core import settings
from app.core.config import get_app_settings
from app.schemas.google_maps_api import DistanceInfo, UserPreferences
from app.schemas.msg import Msg
from app.schemas.place import AutoCompletedPlace, Place
from app.services import user_service
from app.services.constants import PLACETYPE, TravelMode
from app.services.map_services import MapServices, ZeroResultException
from app.services.recommend_services import Recommender

router = APIRouter()

settings = get_app_settings()

map_services = MapServices(
    map_client=googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
)


# TODO: 중간장소 계산만 하는 엔드포인트랑 나눠야함 밑에 여기는 추천만 하는거
@router.post("/request-places/", response_model=List[Place])
def request_places(
    addresses: List[str],
    place_type: PLACETYPE = PLACETYPE.CAFE,
    max_results: int = 5,
    current_user: models.User = Depends(user_service.get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    request meeting places
    """
    try:
        recommend_services = Recommender(
            db,
            current_user,
            map_services,
            UserPreferences(place_type=place_type, return_count=max_results),
        )
        complete_addresses = map_services.get_complete_addresses(
            db, current_user, addresses
        )

        results: List[Place] = recommend_services.recommend_places(
            db,
            complete_addresses,
        )

        return results
    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=204, detail=error_msg)
        else:
            raise HTTPException(status_code=404, detail=f"An error occurred: {error}")


@router.get("/{place_id}", response_model=Place)
async def read_place_by_id(
    place_id: str,
    current_user: models.User = Depends(user_service.get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve place.
    """
    place = crud.place.get_by_place_id(db, id=place_id)

    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    return place


# TODO: 유저 place 타입 기반으로 필터링 하거나 엔드포인트 추가
@router.get("/", response_model=List[Place])
async def read_places(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    Retrieve places.
    """

    places = crud.place.get_multi(db)
    if not places:
        raise HTTPException(status_code=404, detail="Places not found")
    return places


@router.post("/{place_id}/mark", response_model=Msg)
async def mark_interest(
    place_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    mark up place.

    """
    place = crud.place.get_by_place_id(db, id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    if crud.user.has_interest(db, current_user, place):
        raise HTTPException(status_code=400, detail="Already marked place")

    crud.user.mark_interest(db, current_user, place)
    return {"msg": "Place successfully marked"}


@router.delete("/{place_id}/unmark", response_model=Msg)
async def unmark_interest(
    place_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
):
    """
    unmark place.

    """
    place = crud.place.get_by_place_id(db, id=place_id)

    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    if not crud.user.has_interest(db, current_user, place):
        raise HTTPException(status_code=400, detail="Not marked place")

    crud.user.unmark_interest(db, current_user, place)
    return {"msg": "Place successfully unmarked"}


@router.get("/completed-places/{address}", response_model=List[AutoCompletedPlace])
async def read_auto_completed_places(
    address: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
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
            raise HTTPException(status_code=204, detail=error_msg)
        else:
            raise HTTPException(status_code=404, detail=f"An error occurred: {error}")


@router.post("/{destination_id}/get-travel-info", response_model=List[DistanceInfo])
def get_distance_matrix(
    origins: List[str],
    destination_id: str,
    mode: TravelMode = TravelMode.TRANSIT,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(user_service.get_current_active_user),
) -> List[DistanceInfo]:
    try:
        distances = map_services.get_distance_matrix_for_places(
            db, current_user, origins, destination_id, mode, is_place_id=True
        )

        return distances

    except Exception as error:
        if isinstance(error, ZeroResultException):
            error_msg = error.args[0]["detail"]
            raise HTTPException(status_code=204, detail=error_msg)
        else:
            raise HTTPException(status_code=404, detail=f"An error occurred: {error}")
