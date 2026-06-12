"""
services/db.py
SQLAlchemy database configuration and connection helpers.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///kb_articles.db")

Base = declarative_base()


def get_database_url(db_path: str | None = None) -> str:
    """Return a valid SQLAlchemy URL for the configured database or a local SQLite path."""
    if db_path:
        if db_path.startswith("sqlite://"):
            return db_path
        return f"sqlite:///{db_path}"
    return DATABASE_URL


def create_engine_for_url(url: str):
    """Create a SQLAlchemy engine using proper SQLite options when required."""
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, future=True, connect_args=connect_args)


def get_session(db_path: str | None = None):
    """Create a database session bound to the configured engine."""
    url = get_database_url(db_path)
    engine = create_engine_for_url(url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()
