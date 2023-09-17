from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api.deps import get_db
from app.schemas.place import AutoCompletedPlace, Place
from app.services import user_service
from app.services.google_maps_services import GoogleMapsService
from app.services.recommend_services import Recommender

router = APIRouter()

goggle_maps_service = GoogleMapsService()
recommend_service = Recommender()


# TODO: 중간장소 계산만 하는 엔드포인트랑 나눠야함 밑에 여기는 추천만 하는거
@router.post("/request-places/", response_model=List[Place])
async def request_places(addresses: List[str], db: Session = Depends(get_db)):
    """
    request meeting places
    """
    complete_addresses = []
    for address in addresses:
        complete_addresses.append(
            goggle_maps_service.auto_complete_place(address)[0].address
        )

    results: List[Place] = recommend_service.recommend_places(db, complete_addresses)
    return results


# TODO: 여기는 그냥 기본적으로 장소를 받아서 중간 지점 계산
# 장소 받아서 중간 지점 계산
@router.post("/request-midpoint/", response_model=List[Place])
async def request_midpoint(places: List[Place], db: Session = Depends(get_db)):
    pass


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
    return places


@router.post("/{place_id}/mark", response_model=Place)
async def mark_interest(
    place_id: str,
    current_user: models.User = Depends(user_service.get_current_active_user),
    Session=Depends(get_db),
):
    """
    mark up place.

    """
    pass


@router.delete("/{place_id}/unmark", response_model=Place)
async def unmark_interest(
    place_id: str,
    current_user: models.User = Depends(user_service.get_current_active_user),
    Session=Depends(get_db),
):
    """
    unmark place.

    """
    pass


@router.get("/completed-places/{address}", response_model=List[AutoCompletedPlace])
async def read_auto_completed_places(address: str, db: Session = Depends(get_db)):
    """
    retrieve some auto completed places
    """
    places = goggle_maps_service.auto_complete_place(address)
    return places
