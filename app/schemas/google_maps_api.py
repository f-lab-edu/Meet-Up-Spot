from collections import namedtuple
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from app.schemas.place import Place
from app.services.constants import (
    PLACETYPE,
    TrafficModel,
    TransitMode,
    TransitRoutingPreference,
    TravelMode,
)


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


class DistanceMatrixRequest(BaseModel):
    origins: Union[str, List[str]]
    destinations: Union[str, List[str]]
    mode: Optional[TravelMode] = TravelMode.TRANSIT
    region: Optional[str] = None
    language: Optional[str] = "ko"
    avoid: Optional[List[str]] = None
    arrival_time: Optional[int] = None
    departure_time: Optional[Union[int, str]] = "now"  # "now"도 가능하므로 str 포함
    traffic_model: Optional[str] = TrafficModel.BEST_GUESS.value
    transit_mode: Optional[List[str]] = [
        TransitMode.BUS.value,
        TransitMode.SUBWAY.value,
    ]
    transit_routing_preference: Optional[
        str
    ] = TransitRoutingPreference.FEWER_TRANSFERS.value
    units: Optional[str] = None
    is_place_id: Optional[bool] = False


# duration_value는 초단위, distance_value는 미터단위
class DistanceInfo(BaseModel):
    origin: str
    destination: str
    destination_id: Optional[str]
    distance_text: Optional[str]
    distance_value: Optional[int]
    duration_text: Optional[str]
    duration_value: Optional[int]


class UserPreferences:
    place_type: PLACETYPE
    return_count: int
