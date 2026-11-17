"""T25 `user_blocks` — quan hệ chặn nạp sẵn (DDL 6.4-B dòng 406-414).

Bảng chỉ đọc trong S8 (không có API tạo). PK đôi `(blocker_id, blocked_id)`,
CHECK `ck_user_blocks_not_self` cấm tự chặn; FK hai chiều `ON DELETE RESTRICT`.
O6 chốt: lọc **hai chiều** — người mình chặn và người chặn mình đều bị ẩn.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class UserBlock(Base):
    """`blocker_id` chặn `blocked_id`."""

    __tablename__ = "user_blocks"

    blocker_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_user_blocks_blocker_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    blocked_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_user_blocks_blocked_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
