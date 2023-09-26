from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.place import Place, PlaceType
from app.schemas.place import PlaceCreate, PlaceUpdate


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    def get_by_place_id(self, db: Session, *, id: str) -> Optional[Place]:
        return db.query(Place).filter(Place.place_id == id).first()

    def convert_strings_to_place_types(
        self, db: Session, place_types: List[str]
    ) -> List[PlaceType]:
        existing_types = (
            db.query(PlaceType).filter(PlaceType.type_name.in_(place_types)).all()
        )
        existing_types_dict = {item.type_name: item for item in existing_types}

        types = [
            existing_types_dict.get(place_type, PlaceType(type_name=place_type))
            for place_type in place_types
        ]
        return types

    def create(self, db: Session, *, obj_in: PlaceCreate) -> Place:
        db_obj = Place(
            place_id=obj_in.place_id,
            name=obj_in.name,
            address=obj_in.address,
            rating=obj_in.rating,
            user_ratings_total=obj_in.user_ratings_total,
        )
        db_obj.place_types = self.convert_strings_to_place_types(db, obj_in.place_types)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Place, obj_in: Union[PlaceUpdate, Dict[str, Any]]
    ) -> Place:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if update_data.get("place_types"):
            type_obejcts = self.convert_strings_to_place_types(
                db, update_data["place_types"]
            )
            del update_data["place_types"]
            update_data["place_types"] = type_obejcts
        return super().update(db, db_obj=db_obj, obj_in=update_data)


place = CRUDPlace(Place)
