from typing import Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_latlng(
        self, db: Session, *, lat: float, lng: float
    ) -> Optional[Location]:
        return (
            db.query(Location)
            .filter(Location.latitude == lat, Location.longitude == lng)
            .first()
        )

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
        db_obj = Location(
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            compund_code=obj_in.compound_code,
            global_code=obj_in.global_code,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


location = CRUDLocation(Location)
