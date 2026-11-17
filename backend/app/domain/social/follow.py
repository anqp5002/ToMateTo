"""T13 `follows` — theo dõi giữa hai tài khoản (DDL 6.4-B dòng 243-252).

Khoá chính đôi `(follower_id, followee_id)`; CHECK `follower_id <> followee_id`
(O12 đã có trong DDL). Service vẫn phải chặn tự theo dõi trước khi tới đây.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Follow(Base):
    """`follower_id` theo dõi `followee_id`."""

    __tablename__ = "follows"

    follower_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_follows_follower_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    followee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_follows_followee_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("follower_id <> followee_id", name="ck_follows_not_self"),
        # ix_follows_followee (6.4-B): đếm/liệt kê người theo dõi.
        Index("ix_follows_followee", "followee_id", "created_at", "follower_id"),
    )
