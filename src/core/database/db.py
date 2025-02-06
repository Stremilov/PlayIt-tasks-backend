import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.utils.config import settings


engine = create_engine(settings.db.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db_session() -> SessionLocal:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
