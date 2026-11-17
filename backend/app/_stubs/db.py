"""STUB khối nền DB — vai hạ tầng (P1) sẽ thay.

`make_engine`/`session_factory` sync SQLAlchemy 2.0 + psycopg; URL lấy
`DATABASE_URL_TEST` (SPEC S8 r2 §5), thiếu thì dùng giá trị dev trong `.env.example`.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://tomateto:change_me_dev_only@localhost:5433/tomateto_test"
)


def resolve_database_url(url: str | None = None) -> str:
    """Ưu tiên tham số, rồi `DATABASE_URL_TEST`, rồi giá trị dev mặc định."""
    return url or os.environ.get("DATABASE_URL_TEST") or DEFAULT_TEST_DATABASE_URL


def make_engine(url: str | None = None) -> Engine:
    """Tạo engine sync; chưa kết nối cho tới lần dùng đầu tiên."""
    return create_engine(resolve_database_url(url), pool_pre_ping=True, future=True)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Nhà máy `Session` không hết hạn đối tượng sau commit."""
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
