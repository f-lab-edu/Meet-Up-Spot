from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_app_settings

settings = get_app_settings()


def init_db(
    db: Session,
) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)
    fast_api_env = settings.app_env

    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER)
    if not user:
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.user.create(db, obj_in=user_in)  # noqa: F841

    if fast_api_env == "test":
        user = crud.user.get_by_email(db, email=settings.EMAIL_TEST_USER)
        if not user:
            user_in = schemas.UserCreate(
                email=settings.EMAIL_TEST_USER,
                password=settings.EMAIL_TEST_USER_PASSWORD,
                is_superuser=False,
            )
            user = crud.user.create(db, obj_in=user_in)
