from typing import Generator

from fastapi.security import OAuth2PasswordBearer

from app.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
