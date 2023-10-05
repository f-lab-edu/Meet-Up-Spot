from sqlalchemy.orm import Session

from app import crud
from app.core.settings.app import AppSettings
from app.crud.crud_place import CRUDPlaceFactory
from app.models.place import PlaceType
from app.schemas.place import PlaceUpdate
from app.tests.utils.places import create_random_place


def test_create_place(db: Session, settings: AppSettings):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)

    place = create_random_place(db, crud_place=crud_place, name="Test Place")

    assert place.name == "Test Place"


def test_get_by_place_id(db: Session, settings: AppSettings):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)

    place = create_random_place(db, crud_place=crud_place)
    stored_place = crud_place.get_by_place_id(db, id=place.place_id)

    assert stored_place
    assert stored_place.place_id == place.place_id


def test_update_place_name(db: Session, settings: AppSettings):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)

    place = create_random_place(db, crud_place=crud_place, name="Test Place")
    assert place.name == "Test Place"
    new_name = "New Name"

    place_update = PlaceUpdate(name=new_name, place_id=place.place_id, address="Test")
    crud_place.update(db, db_obj=place, obj_in=place_update)
    updated_place = crud_place.get_by_place_id(db, id=place.place_id)
    assert updated_place.name == new_name


def test_update_place_types(db: Session, settings: AppSettings):
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)
    place = create_random_place(db, crud_place=crud_place, types=["cafe"])

    assert place.place_types[0].type_name == "cafe"

    new_types = ["restaurant"]
    place_update = PlaceUpdate(
        name=place.name, place_id=place.place_id, address="Test", place_types=new_types
    )
    crud_place.update(db, db_obj=place, obj_in=place_update)
    updated_place = crud_place.get_by_place_id(db, id=place.place_id)
    assert len(updated_place.place_types) == 1
    assert updated_place.place_types[0].type_name == new_types[0]


def test_convert_strings_to_place_types(db: Session, settings: AppSettings):
    place_types = ["cafe", "restaurant"]
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)
    types = crud_place.convert_strings_to_place_types(db, place_types)
    assert len(types) == 2
    assert type(types[0]) == PlaceType
    assert types[0].type_name == place_types[0]
    assert types[1].type_name == place_types[1]
