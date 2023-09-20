from app.models.place import PlaceType
from app.schemas.google_maps_api import GeocodeResponse
from app.schemas.location import Location
from app.schemas.place import AutoCompletedPlace, Place, PlaceCreate

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

mock_place_dict = {
    "id": 1,
    "place_id": "test_place_id",
    "name": "Test Place",
    "address": "Test Address",
    "user_ratings_total": 100,
    "rating": 4.5,
    "location_id": 1,
    "place_types": ["cafe"],
}
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

mock_place_obj_new = PlaceCreate(
    id=1,
    place_id="test_place_id",
    name="Test Place",
    address="Test Address",
    user_ratings_total=100,
    rating=4.5,
    location_id=1,
    place_types=["cafe"],
)
