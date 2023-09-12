from sqlalchemy.orm import Session

from app.models.google_maps_api_log import GoogleMapsApiLog
from app.schemas.google_maps_api_log import GoogleMapsApiLogCreate


class CRUDGoogleMapsApiLog:
    def create(self, db: Session, *, obj_in: GoogleMapsApiLogCreate) -> GoogleMapsApiLog:
        db_obj = GoogleMapsApiLog(
            user_id=obj_in.user_id,
            status_code=obj_in.status_code,
            reason=obj_in.reason,
            request_url=obj_in.request_url,
            payload=obj_in.payload,
            print_result=obj_in.print_result,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


google_maps_api_log = CRUDGoogleMapsApiLog()
