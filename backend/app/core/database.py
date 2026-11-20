"""Synchronous, request-scoped SQLAlchemy sessions."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(database_url: str) -> Engine:
    """Create a PostgreSQL engine without connecting or creating schema."""
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("PostgreSQL is required.")
    return create_engine(url, pool_pre_ping=True, hide_parameters=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Leave the transaction boundary to the calling service."""
    return sessionmaker(engine, expire_on_commit=False, autoflush=False)
