from sqlalchemy.orm import Session

from app import crud
from app.models.place import PlaceType
from app.tests.utils.places import create_random_place


def test_create_place(db: Session):
    place = create_random_place(db, place_id="test_place_id", name="Test Place")

    assert place.place_id == "test_place_id"
    assert place.name == "Test Place"


def test_get_by_place_id(db: Session):
    place = create_random_place(db)
    stored_place = crud.place.get_by_place_id(db, id=place.place_id)
    assert stored_place
    assert stored_place.place_id == place.place_id


def test_update_place_name(db: Session):
    place = create_random_place(db, name="Test Place")
    assert place.name == "Test Place"
    new_name = "New Name"
    place_update = {"name": new_name}
    crud.place.update(db, db_obj=place, obj_in=place_update)
    updated_place = crud.place.get_by_place_id(db, id=place.place_id)
    assert updated_place.name == new_name


def test_update_place_types(db: Session):
    place = create_random_place(db, types=["cafe"])

    assert place.place_types[0].type_name == "cafe"

    new_types = ["restaurant"]
    place_update = {"place_types": new_types}
    crud.place.update(db, db_obj=place, obj_in=place_update)
    updated_place = crud.place.get_by_place_id(db, id=place.place_id)
    assert len(updated_place.place_types) == 1
    assert updated_place.place_types[0].type_name == new_types[0]


def test_convert_strings_to_place_types(db: Session):
    place_types = ["cafe", "restaurant"]
    types = crud.place.convert_strings_to_place_types(db, place_types)
    assert len(types) == 2
    assert type(types[0]) == PlaceType
    assert types[0].type_name == place_types[0]
    assert types[1].type_name == place_types[1]
