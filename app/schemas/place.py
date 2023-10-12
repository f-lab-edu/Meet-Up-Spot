from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Shared properties
class PlaceBase(BaseModel):
    place_id: str
    name: str | None = None
    address: str
    user_ratings_total: int | None = None
    rating: float | None = None
    place_types: List[str] | None = None
    location_id: int | None = None

    def __eq__(self, other):
        if isinstance(other, PlaceBase):
            return self.place_id == other.place_id
        return False

    def __hash__(self):
        return hash(self.place_id)


class PlaceCreate(PlaceBase):
    place_types: List[str]


class PlaceUpdate(PlaceBase):
    pass


class PlaceType(BaseModel):
    type_name: str


class PlaceInDBBase(PlaceBase):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None


class Place(PlaceInDBBase):
    place_types: List[PlaceType]


class PlaceInDB(PlaceInDBBase):
    pass


class AutoCompletedPlace(PlaceBase):
    main_address: str
    secondary_address: str
