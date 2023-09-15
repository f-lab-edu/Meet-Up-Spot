from sqlalchemy import Column, ForeignKey, Integer, Table

from app.db.base_class import Base

# pylint: disable=no-member
user_place_association = Table(
    "user_place_associations",
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
