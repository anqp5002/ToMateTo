"""Shared sync connection factory. Repositories never commit caller transactions."""

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url


def database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required; no implicit database target")
    url = make_url(value)
    if url.drivername != "postgresql+psycopg":
        raise ValueError("Use postgresql+psycopg (sync Psycopg 3)")
    return value


def make_engine() -> Engine:
    return create_engine(
        database_url(),
        pool_pre_ping=True,
        connect_args={"options": "-c timezone=UTC -c search_path=public,pg_catalog"},
    )


def require_test_reset() -> None:
    name = make_url(database_url()).database or ""
    if not name.endswith("_test") or os.environ.get("ALLOW_TEST_DATABASE_RESET") != "1":
        raise RuntimeError("Reset needs a *_test database and ALLOW_TEST_DATABASE_RESET=1")
