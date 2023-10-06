from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.associations import user_interested_place_association


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
    searched_place_relations = relationship("UserSearchedPlace", back_populates="user")

    @property
    def preferred_types(self):
        # 각 관심 장소의 모든 타입들을 하나의 집합으로 합칩니다.
        types_from_interested = {
            ptype for place in self.interested_places for ptype in place.place_types
        }

        # 각 검색 기록의 모든 타입들을 하나의 집합으로 합칩니다.
        types_from_searched = {
            ptype
            for searched_place in self.searched_places
            for ptype in searched_place.place_types
        }

        # 두 집합을 합칩니다.
        combined_types = types_from_interested.union(types_from_searched)

        return list(combined_types)

    @property
    def searched_places(self):
        return [relation.place for relation in self.searched_place_relations]
