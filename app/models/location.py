from sqlalchemy import Column, Float, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.associations import user_current_location_association


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    compound_code = Column(String(255))
    global_code = Column(String(255))

    places = relationship("Place", back_populates="location")

    users = relationship(
        "User",
        secondary=user_current_location_association,
        back_populates="location_history",
    )


Index("idx_latitude_longitude", Location.latitude, Location.longitude)
