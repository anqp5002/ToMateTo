"""Khai báo `Base` dùng chung cho mọi thực thể SQLAlchemy (DOC 7.4-A.3 §2.2).

Quy ước đặt tên bám DDL 6.4-B: `pk_`, `uq_`, `ck_`, `fk_`, `ix_`. Thực thể vẫn
khai báo tên tường minh khi DDL đặt tên khác quy ước (ví dụ `uq_collections_one_default`).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Lớp gốc ORM; metadata mang naming convention của chuẩn DB."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
