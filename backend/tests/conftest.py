"""Fixture CSDL PostgreSQL thật cho toàn bộ test backend (SPEC S8 r2 §5).

Không SQLite, không mock: mỗi session tạo `tomateto_test` nếu thiếu, dựng schema
bằng DDL nguyên văn DOC 6.4-B (T12–T17, T25 + bảng cha), mỗi test chạy trong một
transaction rồi rollback. Thiếu CSDL thì báo rõ và bỏ qua test cần DB, không
xanh giả.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import NoReturn

import psycopg
import pytest
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from tests.support.ddl import apply_ddl

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://tomateto:change_me_dev_only@localhost:5433/tomateto_test"
)
_DATABASE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _read_dotenv(path: Path) -> dict[str, str]:
    """Đọc `.env` dạng KEY=VALUE đơn giản; không ghi đè biến môi trường."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


def resolve_test_database_url() -> str:
    """Biến môi trường → `.env` ở gốc repo → giá trị dev trong `.env.example`."""
    return (
        os.environ.get("DATABASE_URL_TEST")
        or _read_dotenv(REPO_ROOT / ".env").get("DATABASE_URL_TEST")
        or DEFAULT_TEST_DATABASE_URL
    )


def _libpq_url(url: URL) -> str:
    """URL cho psycopg (bỏ hậu tố driver `+psycopg`)."""
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def _skip_without_postgres(url: URL, error: BaseException) -> NoReturn:
    pytest.skip(
        "Không kết nối được PostgreSQL "
        f"({url.host}:{url.port}/{url.database}). Docker có thể đang tắt: chạy"
        " `docker compose up -d postgres` rồi `cd backend && pytest -q`. Không dùng"
        f" SQLite/mock. Lỗi gốc: {type(error).__name__}",
    )


def ensure_database(url_text: str) -> None:
    """Tạo database test nếu thiếu, bằng kết nối autocommit vào DB `postgres`."""
    url = make_url(url_text)
    database = url.database or ""
    if not _DATABASE_NAME.match(database):
        pytest.fail(f"Tên database test không hợp lệ: {database!r}")
    admin_url = url.set(database="postgres")
    try:
        with psycopg.connect(_libpq_url(admin_url), autocommit=True) as connection:
            exists = connection.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
            ).fetchone()
            if exists is None:
                # Tên database đã được kiểm bằng _DATABASE_NAME, không đến từ input test.
                connection.execute(f'CREATE DATABASE "{database}"')  # noqa: S608
    except psycopg.errors.DuplicateDatabase:
        return
    except psycopg.OperationalError as error:
        _skip_without_postgres(admin_url, error)


@pytest.fixture(scope="session")
def database_url() -> str:
    """URL CSDL test đang dùng cho session này."""
    return resolve_test_database_url()


@pytest.fixture(scope="session")
def db_engine(database_url: str) -> Iterator[Engine]:
    """Engine session-scoped; schema được dựng lại một lần từ DDL 6.4-B."""
    ensure_database(database_url)
    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    try:
        apply_ddl(engine)
    except psycopg.OperationalError as error:
        engine.dispose()
        _skip_without_postgres(make_url(database_url), error)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_connection(db_engine: Engine) -> Iterator[Connection]:
    """Kết nối đang mở transaction; teardown luôn rollback để test sạch."""
    connection = db_engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


@pytest.fixture()
def db_session(db_connection: Connection) -> Iterator[Session]:
    """Session gắn vào transaction của test; `commit()` chỉ giải phóng savepoint."""
    factory: sessionmaker[Session] = sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()
