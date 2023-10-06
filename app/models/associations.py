from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# pylint: disable=no-member
user_interested_place_association = Table(
    "user_interested_place_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id", ondelete="CASCADE")),
    Column("place_id", Integer, ForeignKey("place.id", ondelete="CASCADE")),
)


# pylint: disable=no-member
place_type_association = Table(
    "place_type_association",
    Base.metadata,
    Column("place_id", Integer, ForeignKey("place.id", ondelete="CASCADE")),
    Column("place_type_id", Integer, ForeignKey("placetype.id", ondelete="CASCADE")),
)


class UserSearchedPlace(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    place_id = Column(Integer, ForeignKey("place.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="searched_place_relations")
    place = relationship("Place", back_populates="searched_user_relations")
