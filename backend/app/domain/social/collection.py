"""T14 `collections` — bộ sưu tập bài của một người (DDL 6.4-B dòng 254-266).

Ràng buộc đáng nhớ:
- `UNIQUE (user_id, name_normalized)` — hai bộ không trùng tên trong một chủ.
- `uq_collections_one_default` — partial UNIQUE `(user_id) WHERE is_default=true`,
  CSDL bảo đảm **tối đa một** bộ mặc định; "có đúng một" là việc của service.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Collection(Base):
    """Một bộ sưu tập; bộ `is_default=True` là "Đã lưu" của chủ."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_collections_user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "name_normalized", name="uq_collections_user_id_name_normalized"
        ),
        CheckConstraint(
            "btrim(name) <> '' AND btrim(name_normalized) <> ''",
            name="ck_collections_name",
        ),
        # Partial unique: tối đa một bộ mặc định mỗi chủ (6.4-B dòng 437).
        Index(
            "uq_collections_one_default",
            "user_id",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
        Index("ix_collections_owner_created", "user_id", "created_at", "id"),
    )
