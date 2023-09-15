from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.associations import place_type_association, user_place_association


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    google_maps_api_logs = relationship("GoogleMapsApiLog", back_populates="user")
    places = relationship(
        "Place", secondary=user_place_association, back_populates="users"
    )