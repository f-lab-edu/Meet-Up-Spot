from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models import Location
from app.models.associations import (
    user_current_location_association,
    user_interested_place_association,
)


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    google_maps_api_logs = relationship("GoogleMapsApiLog", back_populates="user")
    interested_places = relationship(
        "Place", secondary=user_interested_place_association, back_populates="users"
    )
    search_history_relations = relationship("UserSearchHistory", back_populates="user")

    location_history = relationship(
        "Location", secondary=user_current_location_association, back_populates="users"
    )

    @property
    def preferred_types(self):
        types_from_interested = {
            ptype for place in self.interested_places for ptype in place.place_types
        }

        return list(types_from_interested)

    @property
    def searched_addresses(self):
        return [relation.address for relation in self.search_history_relations]

    @property
    def latest_location(self) -> Location:
        return self.location_history[-1] if self.location_history else None
