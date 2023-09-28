from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_app_settings

settings = get_app_settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
