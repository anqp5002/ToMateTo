"""T16 `reports` — báo cáo bài viết (DDL 6.4-B dòng 279-294).

- `post_id` nullable, FK `posts.id` **ON DELETE SET NULL**: bài bị xoá thì báo cáo
  còn, chỉ mất liên kết sống.
- `original_post_id` **không FK**: giữ mã bài gốc làm lịch sử dù bài đã biến mất.
- `evidence_snapshot` JSONB: bản chụp nội dung tại thời điểm báo cáo, bất biến.
- Không có cột `is_hidden`: báo cáo không tự ẩn bài (5.3-B T16).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Report(Base):
    """Một lượt báo cáo của `reporter_id` cho bài `original_post_id`."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=False), primary_key=True)
    reporter_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_reports_reporter_id", ondelete="RESTRICT"),
        nullable=False,
    )
    post_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", name="fk_reports_post_id", ondelete="SET NULL"),
        nullable=True,
    )
    original_post_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
