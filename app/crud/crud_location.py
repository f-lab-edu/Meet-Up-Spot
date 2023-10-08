from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
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


location = CRUDLocation(Location)
