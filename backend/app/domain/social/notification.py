"""T17 `notifications` — hộp thông báo của người dùng (DDL 6.4-B dòng 297-310).

`read_at` (không phải cờ `read`) giữ cả thời điểm đọc; `type` chỉ LIKE/SAVE/FOLLOW
theo CHECK của DDL. Hai index phục vụ đúng hai truy vấn của hộp thư:
`ix_notifications_inbox` cho trang `(created_at DESC, id DESC)` và
`ix_notifications_unread` (partial) cho tổng chưa đọc.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Identity, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class NotificationType(StrEnum):
    """Ba loại thông báo mà CHECK `ck_notifications_type` chấp nhận."""

    LIKE = "LIKE"
    SAVE = "SAVE"
    FOLLOW = "FOLLOW"


class Notification(Base):
    """Một thông báo gửi tới `user_id`, có thể kèm `actor_id`/`post_id` (đã xoá → NULL)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_notifications_user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    actor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_notifications_actor_id", ondelete="SET NULL"),
        nullable=True,
    )
    post_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", name="fk_notifications_post_id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            native_enum=False,
            length=8,
            create_constraint=False,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # DDL tạo CHECK trong bảng; model không tạo lại để tránh lệch tên.
        Index("ix_notifications_inbox", "user_id", text("created_at DESC"), text("id DESC")),
        Index(
            "ix_notifications_unread",
            "user_id",
            postgresql_where=text("read_at IS NULL"),
        ),
    )

    def mark_read(self, now: datetime) -> None:
        """Đánh dấu đã đọc tại `now`; gọi lần hai không đổi dấu thời gian cũ."""
        if self.read_at is None:
            self.read_at = now
