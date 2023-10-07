from sqlalchemy import Column, ForeignKey, Integer, String, Table
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


class UserSearchHistory(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    address = Column(String(255), nullable=False)

    user = relationship("User", back_populates="search_history_relations")
