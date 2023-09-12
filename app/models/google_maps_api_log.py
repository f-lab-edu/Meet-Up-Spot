import json

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GoogleMapsApiLog(Base):
    __tablename__ = "google_maps_api_logs"

    id = Column(Integer, primary_key=True, index=True)
    status_code = Column(Integer, nullable=False)
    reason = Column(String)
    request_url = Column(String, nullable=False)
    payload = Column(String)
    print_result = Column(String)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="google_maps_api_logs")
