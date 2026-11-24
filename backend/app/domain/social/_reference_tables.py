"""Social shares the real T01 User mapping with group 4.1.

T09 remains a minimal reference until the Content entity is integrated.
Schema creation uses DOC 6.4-B, not ORM create_all.
"""

from __future__ import annotations

from typing import cast

from sqlalchemy import BigInteger, Boolean, Column, Table

from app.domain.base import Base
from app.domain.identity.user import User

#: T01: reuse the same table, so metadata never registers users twice.
users_table: Table = cast(Table, User.__table__)

#: T09 `posts` — cột cần cho FK và cho bộ lọc hiển thị/chặn.
posts_table: Table = Table(
    "posts",
    Base.metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger, nullable=False),
    Column("is_hidden", Boolean, nullable=False, server_default="false"),
    extend_existing=True,
)
