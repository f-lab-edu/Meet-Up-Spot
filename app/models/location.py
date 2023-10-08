from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Location(Base):
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    compound_code = Column(String(255), index=True)
    global_code = Column(String(255), index=True)

    places = relationship("Place", back_populates="location")
