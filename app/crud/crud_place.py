from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.core.settings.base import AppEnvTypes
from app.crud.base import CRUDBase
from app.models.associations import place_type_association
from app.models.place import Place, PlaceType
from app.schemas.place import PlaceCreate, PlaceUpdate

app_settings = get_app_settings()


class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    def get_by_place_id(self, db: Session, *, id: str) -> Optional[Place]:
        return db.query(Place).filter(Place.place_id == id).first()

    def get_by_place_ids(self, db: Session, place_ids: List[int]) -> List[Place]:
        return db.query(Place).filter(Place.place_id.in_(place_ids)).all()

    def convert_strings_to_place_types(
        self, db: Session, place_types: List[str]
    ) -> List[PlaceType]:
        existing_types = (
            db.query(PlaceType).filter(PlaceType.type_name.in_(place_types)).all()
        )

        existing_types_dict = {item.type_name: item for item in existing_types}

        new_types = [
            PlaceType(type_name=place_type)
            for place_type in place_types
            if place_type not in existing_types_dict
        ]

        return existing_types, new_types

    def process_place_types(self, db, place_list):
        all_place_types = set(
            place_type for place in place_list for place_type in place["place_types"]
        )

        existing_types, new_types = self.convert_strings_to_place_types(
            db, list(all_place_types)
        )

        db.bulk_insert_mappings(
            PlaceType, [jsonable_encoder(place_type) for place_type in new_types]
        )
        db.flush()

        added_place_types = (
            db.query(PlaceType)
            .filter(
                PlaceType.type_name.in_(
                    [place_type.type_name for place_type in new_types]
                )
            )
            .all()
        )

        combined_types_dict = {
            item.type_name: item for item in existing_types + added_place_types
        }

        return combined_types_dict

    def _prepare_association_data(self, place_list, combined_types_dict):
        """Prepare the association data between places and their types."""
        association_data = []
        for place in place_list:
            for place_type in place["place_types"]:
                association_data.append(
                    {
                        "place_id": place["place_id"],
                        "place_type_id": combined_types_dict[place_type].id,
                    }
                )
        return association_data

    def create(self, db: Session, *, obj_in: PlaceCreate) -> Place:
        db_obj = Place(
            place_id=obj_in.place_id,
            name=obj_in.name,
            address=obj_in.address,
            rating=obj_in.rating,
            location_id=obj_in.location_id,
            user_ratings_total=obj_in.user_ratings_total,
        )
        existing_types, new_types = self.convert_strings_to_place_types(
            db, obj_in.place_types
        )
        db_obj.place_types = existing_types + new_types

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
            existing_types, new_types = self.convert_strings_to_place_types(
                db, update_data["place_types"]
            )
            del update_data["place_types"]
            update_data["place_types"] = existing_types + new_types
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def bulk_insert(self, db, place_list: List[dict]):
        combined_types_dict = self.process_place_types(db, place_list)

        db.bulk_insert_mappings(Place, place_list)

        association_data = self._prepare_association_data(
            place_list, combined_types_dict
        )

        db.execute(place_type_association.insert(), association_data)
        db.commit()


class MemoryCRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    def __init__(self):
        self._places = set([])

    @property
    def places(self):
        return self._places

    @places.setter
    def places(self, value):
        self._places = set(value)

    def get_by_place_id(self, db: Session = None, *, id: str) -> Optional[Place]:
        return next((place for place in self.places if place.place_id == id), None)

    def get_by_place_ids(self, db: Session, place_ids: List[int]) -> List[Place]:
        return [place for place in self.places if place.place_id in place_ids]

    def create(self, db=None, obj_in=None):
        self._places.add(obj_in)

        return obj_in

    def update(self, db=None, db_obj=None, obj_in=None):
        self._places.remove(db_obj)
        self._places.add(obj_in)

        return obj_in

    @property
    def list(self):
        return list(self._places)

    def bulk_insert(self, db, place_list: List[dict]):
        return self._places.update([PlaceCreate(**place) for place in place_list])


class CRUDPlaceFactory:
    @staticmethod
    def get_instance(
        env: str, use_memory: bool = True
    ) -> Union[CRUDPlace, MemoryCRUDPlace]:
        if env == AppEnvTypes.test and use_memory:
            return MemoryCRUDPlace()
        return CRUDPlace(Place)


place = CRUDPlaceFactory.get_instance(app_settings.APP_ENV)
