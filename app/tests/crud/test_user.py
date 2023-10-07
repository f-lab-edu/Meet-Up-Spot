from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.core.settings.app import AppSettings
from app.crud.crud_place import CRUDPlaceFactory
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.places import create_random_place
from app.tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    authenticated_user = crud.user.authenticate(db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.user.authenticate(db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    is_active = crud.user.is_active(user)
    assert is_active is True


def test_check_if_user_is_active_inactive(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, disabled=True)
    user = crud.user.create(db, obj_in=user_in)
    is_active = crud.user.is_active(user)
    assert is_active


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(db, obj_in=user_in)
    is_superuser = crud.user.is_superuser(user)
    assert is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.user.create(db, obj_in=user_in)
    is_superuser = crud.user.is_superuser(user)
    assert is_superuser is False


def test_get_user(db: Session) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = crud.user.create(db, obj_in=user_in)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(db, obj_in=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    crud.user.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = crud.user.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)


def test_mark_unmark_interest(db: Session, settings: AppSettings) -> None:
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(db, obj_in=user_in)

    place = create_random_place(db, crud_place)

    user = crud.user.mark_interest(db, user=user, place=place)
    assert user
    assert place in user.interested_places
    user = crud.user.unmark_interest(db, user=user, place=place)
    assert user
    assert place not in user.interested_places
    user = crud.user.mark_interest(db, user=user, place=place)
    assert user
    assert place in user.interested_places
    user = crud.user.unmark_interest(db, user=user, place=place)
    assert user
    assert place not in user.interested_places

    db.delete(user)
    db.delete(place)
    db.commit()


def test_has_interest(db: Session, settings: AppSettings) -> None:
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)

    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.user.create(db, obj_in=user_in)
    place = create_random_place(db, crud_place)

    user = crud.user.mark_interest(db, user=user, place=place)
    assert user
    assert crud.user.has_interest(db, user=user, place=place)
    user = crud.user.unmark_interest(db, user=user, place=place)
    assert user
    assert not crud.user.has_interest(db, user=user, place=place)


def test_add_search_history(db: Session, normal_user, settings: AppSettings) -> None:
    crud_place = CRUDPlaceFactory.get_instance(settings.APP_ENV, False)
    place = create_random_place(db, crud_place)
    crud.user.add_search_history(db, normal_user, place.address)
    assert len(normal_user.search_history_relations) == 1
    assert place.address == normal_user.search_history_relations[0].address
    db.delete(normal_user)
    db.commit()
    db.delete(place)
    db.commit()
