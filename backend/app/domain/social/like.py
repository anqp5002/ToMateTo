"""T12 `likes` — một người thích một bài (DDL 6.4-B dòng 233-241).

Khoá chính đôi `(user_id, post_id)`: thích trùng không sinh dòng thứ hai.
FK `post_id` xoá theo bài (CASCADE); FK `user_id` chặn xoá tài khoản (RESTRICT).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Like(Base):
    """Một lượt thích của `user_id` lên `post_id`."""

    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_likes_user_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", name="fk_likes_post_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # ix_likes_post_created (6.4-B): đếm lượt thích theo bài.
        Index("ix_likes_post_created", "post_id", "created_at"),
    )
