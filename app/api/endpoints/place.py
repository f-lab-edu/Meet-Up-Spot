from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.place import Place
from app.services.google_maps_services import GoogleMapsService
from app.services.recommend_services import Recommender

router = APIRouter()

goggle_maps_service = GoogleMapsService()
recommend_service = Recommender()


@router.post("/request_places/", response_model=List[Place])
async def request_places(addresses: List[str], db: Session = Depends(get_db)):
    """
    유저에게 주소를 입력받아 만남 장소를 추천하는 API 엔드포인트
    """
    complete_addresses = []
    for address in addresses:
        complete_addresses.append(
            goggle_maps_service.auto_complete_place(address)[0]["description"]
        )

    results: List[Place] = recommend_service.recommend_places(db, complete_addresses)
    return results


@router.get("/select_place/")
async def select_place(place_id: str, db: Session = Depends(get_db)):
    """
    유저가 선택한 장소를 저장하는 API 엔드포인트
    """
    pass
    # 어차피 db에 있는것만 선택할 수 있으니까 그냥 place_id만 받아서 저장하면 될듯
    # place_id로 장소를 검색해서 있으면 저장하고 없으면 에러를 반환하면 될듯
