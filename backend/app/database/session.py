from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from .models import Base


def make_engine(url):
    if not url:
        raise ValueError("DATABASE_URL is required; configure it before migrating or seeding")
    # Accept the previous PostgreSQL URL spelling while selecting psycopg 3.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    options = {"connect_timeout": 5} if url.startswith("postgresql") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=options)


engine = make_engine(settings.database_url) if settings.database_url else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    if engine is None:
        raise HTTPException(status_code=503, detail="Metadata database is not configured")
    with SessionLocal() as session:
        yield session
