from typing import List

from pydantic import BaseModel

from app.schemas.place import Place


class GeocodeResponse(BaseModel):
    latitude: float
    longitude: float


class ReverseGeocodeRequest(BaseModel):
    latitude: float
    longitude: float


class ReverseGeocodeResponse(BaseModel):
    address: str


class RequestSpotRequest(BaseModel):
    addresses: str


class RequestSpotResponse(BaseModel):
    results: List[Place]
