from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Shared properties
class PlaceBase(BaseModel):
    place_id: str
    name: str
    address: str
    location_id: int
    user_ratings_total: int
    address: str
    rating: float


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
