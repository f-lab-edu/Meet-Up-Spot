from random import randint
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.models.place import PlaceType
from app.schemas.google_maps_api import GeocodeResponse
from app.schemas.location import Location, LocationCreate
from app.schemas.place import AutoCompletedPlace, Place, PlaceCreate
from app.tests.utils.utils import random_lower_string

mock_place_obj = Place(
    id=1,
    place_id="test_place_id",
    name="Test Place",
    address="Test Address",
    user_ratings_total=100,
    rating=4.5,
    location_id=1,
    place_types=[{"id": 1, "type_name": "cafe"}],
)
mock_place_obj2 = Place(
    id=1,
    place_id="test_place_id2",
    name="Test Place2",
    address="Test Address2",
    user_ratings_total=100,
    rating=4.5,
    location_id=1,
    place_types=[{"id": 1, "type_name": "cafe"}],
)


places_list = [mock_place_obj, mock_place_obj2]

auto_completed_place_schema = AutoCompletedPlace(
    address="Test Address",
    main_address="Test Address",
    secondary_address="Test secondary address",
    place_id="test_place_id",
)


test_address = "Test Address"

mock_geocode_response = GeocodeResponse(latitude=123.456, longitude=789.101)

mock_geocode_response = [
    {
        "geometry": {"location": {"lat": 123.456, "lng": 789.101}},
        "plus_code": {"compound_code": "test_compuond", "global_code": "test_global"},
    }
]
mock_place_type_obj = PlaceType(id=1, type_name="cafe")

mock_place_api_response = {
    "place_id": "test_place_id",
    "name": "Test Place",
    "vicinity": "Test Address",
    "user_ratings_total": 100,
    "rating": 4.5,
    "types": ["cafe"],
}

mock_location = Location(
    id=1,
    latitude=123.456,
    longitude=789.101,
    compound_code="test_compound_code",
    global_code="test_global_code",
)
location_in = {
    "latitude": 123.456,
    "longitude": 789.101,
    "compound_code": "test_compound_code",
    "global_code": "test_global_code",
}


def create_random_location(db: Session):
    latitude = randint(10, 1000)
    longitude = randint(10, 1000)
    compound_code = f"compound_code_{random_lower_string()}"
    global_code = f"global_code_{random_lower_string()}"
    location_in = LocationCreate(
        latitude=latitude,
        longitude=longitude,
        compound_code=compound_code,
        global_code=global_code,
    )

    return crud.location.create(db, obj_in=location_in)


def create_random_place(
    db: Session,
    place_id: str = None,
    name: str = None,
    address: str = None,
    location_id: int = None,
    types: List[any] = None,
):
    place_id = place_id or f"test_{random_lower_string()}"
    name = name or f"Test Place {random_lower_string()}"
    address = address or f"Test Address {random_lower_string()}"
    user_ratings_total = randint(1, 1000)
    rating = randint(1, 5)
    location_id = location_id or create_random_location(db).id
    place_types = types or ["cafe"]
    place_in = PlaceCreate(
        place_id=place_id,
        name=name,
        address=address,
        user_ratings_total=user_ratings_total,
        rating=rating,
        location_id=location_id,
        place_types=place_types,
    )

    return crud.place.create(db, obj_in=place_in)


def create_location_place(db):
    location_create = LocationCreate(
        latitude=123.456,
        longitude=789.101,
        compound_code="test_compound_code",
        global_code="test_global_code",
    )

    location = crud.location.create(db, obj_in=location_create)

    place_create = PlaceCreate(
        place_id="test_place_id",
        name="Test Place",
        address="Test Address",
        user_ratings_total=100,
        rating=4.5,
        location_id=location.id,
        place_types=["cafe"],
    )
    place = crud.place.create(db, obj_in=place_create)

    return location, place
