from typing import List, Optional, Tuple, Union

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.core.settings.base import AppEnvTypes
from app.crud.base import CRUDBase
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate

app_settings = get_app_settings()


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_latlng(
        self, db: Session, *, lat: float, lng: float
    ) -> Optional[Location]:
        return (
            db.query(Location)
            .filter(Location.latitude == lat, Location.longitude == lng)
            .first()
        )

    def get_by_latlng_list(
        self, db: Session, latlng_list: List[Tuple[float, float]]
    ) -> List[Location]:
        or_conditions = [
            and_(Location.latitude == lat, Location.longitude == lng)
            for lat, lng in latlng_list
        ]
        return db.query(Location).filter(or_(*or_conditions)).all()

    def get_by_plus_code(
        self, db: Session, *, global_code: str, compound_code: str
    ) -> Optional[Location]:
        return (
            db.query(Location)
            .filter(
                Location.global_code == global_code,
                Location.compound_code == compound_code,
            )
            .first()
        )

    def create(self, db: Session, *, obj_in: LocationCreate) -> Location:
        return super().create(db, obj_in=obj_in)

    def bulk_insert(self, db: Session, location_list: List[dict]):
        db.bulk_insert_mappings(Location, location_list)
        db.commit()


class MemoryCRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def __init__(self):
        self._locations = set([])

    @property
    def locations(self):
        return self._locations

    @locations.setter
    def locations(self, value):
        self._locations = value

    def get_by_latlng_list(
        self, db: Session, latlng_list: List[Tuple[float, float]]
    ) -> List[Location]:
        return [
            location
            for location in self._locations
            if (location.latitude, location.longitude) in latlng_list
        ]

    @property
    def list(self):
        return list(self.locations)

    def create(self, db=None, obj_in=None):
        self._locations.add(obj_in)

        return obj_in

    def bulk_insert(self, db, location_list: List[dict]):
        self._locations.update([LocationCreate(**place) for place in location_list])


class CRUDLocationFactory:
    @staticmethod
    def get_instance(
        env: str, use_memory: bool = True
    ) -> Union[CRUDLocation, MemoryCRUDLocation]:
        if env == AppEnvTypes.test and use_memory:
            return MemoryCRUDLocation()
        return CRUDLocation(Location)


location = CRUDLocationFactory.get_instance(app_settings.APP_ENV)
