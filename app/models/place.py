from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.associations import place_type_association, user_place_association

# pylint: disable=no-member


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
    users = relationship(
        "User", secondary=user_place_association, back_populates="places"
    )
    place_types = relationship(
        "PlaceType", secondary=place_type_association, back_populates="places"
    )


class PlaceType(Base):
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(255), nullable=False, unique=True, index=True)

    places = relationship(
        "Place", secondary=place_type_association, back_populates="place_types"
    )