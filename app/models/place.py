from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Place(Base):
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    rating = Column(Float, default=0.0)
    user_ratings_total = Column(Integer, default=0)

    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))

    location = relationship("Location", back_populates="places")
    user = relationship("User", back_populates="places")
