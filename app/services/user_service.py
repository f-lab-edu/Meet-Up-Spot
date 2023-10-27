from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.deps import get_db
from app.core import security
from app.core.config import get_app_settings
from app.schemas.location import LocationBase

settings = get_app_settings()

from http import HTTPStatus

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User not found")
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def update_user_location_if_needed(
    db: Session, user: models.User, location: LocationBase
):
    if not user.latest_location or (
        user.latest_location.latitude != location.latitude
        or user.latest_location.longitude != location.longitude
    ):
        crud.user.add_location_history(db, user, location.latitude, location.longitude)
