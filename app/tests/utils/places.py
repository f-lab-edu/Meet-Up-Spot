from random import randint
from typing import List

from sqlalchemy.orm import Session

from app import crud
from app.models.place import PlaceType
from app.schemas.google_maps_api import DistanceInfo, GeocodeResponse, UserPreferences
from app.schemas.location import Location, LocationCreate
from app.schemas.place import AutoCompletedPlace, Place, PlaceCreate
from app.services.constants import PLACETYPE
from app.tests.utils.utils import random_lower_string

mock_place_obj = Place(
    id=1,
    place_id=random_lower_string(),
    name="Test Place",
    address=random_lower_string(),
    user_ratings_total=100,
    rating=4.5,
    location_id=1,
    place_types=[{"id": 1, "type_name": "cafe"}],
)
mock_place_obj2 = Place(
    id=1,
    place_id=random_lower_string(),
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


distance_info_list = [
    DistanceInfo(
        origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
        destination_id="ChIJN1t_tDeuEmsRUsoyG83frY1",
        destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
        distance_text="2.2 km",
        distance_value=100,
        duration_text="22분",
        duration_value=100,
    ),
    DistanceInfo(
        origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
        destination_id="ChIJN1t_tDeuEmsRUsoyG83frY2",
        destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        distance_text="29.4 km",
        distance_value=1000,
        duration_text="53분",
        duration_value=1000,
    ),
    DistanceInfo(
        origin="대한민국 서울특별시 양재역",
        destination_id="ChIJN1t_tDeuEmsRUsoyG83frY1",
        destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
        distance_text="12.9 km",
        distance_value=500,
        duration_text="13분",
        duration_value=500,
    ),
    DistanceInfo(
        origin="대한민국 서울특별시 양재역",
        destination_id="ChIJN1t_tDeuEmsRUsoyG83frY2",
        destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        distance_text="15.5 km",
        distance_value=300,
        duration_text="34분",
        duration_value=300,
    ),
]
distance_info_list_no_id = [
    DistanceInfo(
        origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
        destination_id=None,
        destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
        distance_text="2.2 km",
        distance_value=2186,
        duration_text="22분",
        duration_value=1299,
    ),
    DistanceInfo(
        origin="대한민국 경기도 성남시 분당구 성남대로 지하 601 서현",
        destination_id=None,
        destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        distance_text="29.4 km",
        distance_value=29450,
        duration_text="53분",
        duration_value=3168,
    ),
    DistanceInfo(
        origin="대한민국 서울특별시 양재역",
        destination_id=None,
        destination="대한민국 경기도 성남시 분당구 삼평동 판교역로 160 판교역",
        distance_text="12.9 km",
        distance_value=12881,
        duration_text="13분",
        duration_value=805,
    ),
    DistanceInfo(
        origin="대한민국 서울특별시 양재역",
        destination_id=None,
        destination="대한민국 서울특별시 중구 소공동 세종대로18길 2 서울역",
        distance_text="15.5 km",
        distance_value=15475,
        duration_text="34분",
        duration_value=2065,
    ),
]

places_list_related_to_distance_info = [
    Place(
        place_id="ChIJN1t_tDeuEmsRUsoyG83frY1",
        name="판교역",
        address="대한민국 경기도 성남시 분당구 삼평동 판교역로 160",
        user_ratings_total=100,
        rating=4.5,
        place_types=[{"id": 1, "type_name": "cafe"}],
    ),
    Place(
        place_id="ChIJN1t_tDeuEmsRUsoyG83frY2",
        name="서울역",
        address="대한민국 서울특별시 중구 소공동 세종대로18길 2",
        user_ratings_total=100,
        rating=4.5,
        place_types=[{"id": 1, "type_name": "cafe"}],
    ),
]

user_preferences = UserPreferences(place_type=PLACETYPE.CAFE, return_count=2)
