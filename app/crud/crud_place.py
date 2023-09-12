from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.place import Place
from app.schemas.place import PlaceCreate, PlaceUpdate


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    def get_by_place_id(self, db: Session, *, id: str) -> Optional[Place]:
        return db.query(Place).filter(Place.place_id == id).first()

    def create(self, db: Session, *, obj_in: PlaceCreate) -> Place:
        db_obj = Place(
            place_id=obj_in.place_id,
            name=obj_in.name,
            address=obj_in.address,
            location_id=obj_in.location_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


place = CRUDPlace(Place)
