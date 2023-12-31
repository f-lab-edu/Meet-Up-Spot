from datetime import timedelta
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import get_app_settings
from app.core.security import get_password_hash
from app.core.settings.app import AppSettings
from app.services import user_service
from app.utils import (
    generate_password_reset_token,
    parsed_email_password_reset_token,
    send_reset_password_email,
)

router = APIRouter()
settings = get_app_settings()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Incorrect email or password"
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return schemas.Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer",
    )


@router.post("/login/test-token", response_model=schemas.User)
def test_token(
    current_user: models.User = Depends(user_service.get_current_user),
) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = parsed_email_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}
