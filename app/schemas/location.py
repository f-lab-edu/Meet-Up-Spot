from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# Shared properties
class LocationBase(BaseModel):
    latitude: float
    longitude: float


# Properties to receive via API on creation
class LocationCreate(LocationBase):
    compound_code: str
    global_code: str
    latitude: float
    longitude: float


class LocationUpdate(LocationBase):
    pass


class LocationInDBBase(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None


# Additional properties to return via API
class Location(LocationInDBBase):
    pass


# Additional properties stored in DB
class LocationInDB(LocationInDBBase):
    pass
