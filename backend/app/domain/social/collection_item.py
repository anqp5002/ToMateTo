"""T15 `collection_items` — bài nằm trong bộ (DDL 6.4-B dòng 268-276).

Khoá chính đôi `(collection_id, post_id)`; `added_at` là khoá sắp của con trỏ
`(added_at DESC, post_id DESC)` nên hai bài cùng giây vẫn phân trang được.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class CollectionItem(Base):
    """Một bài `post_id` được thêm vào bộ `collection_id`."""

    __tablename__ = "collection_items"

    collection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("collections.id", name="fk_collection_items_collection_id", ondelete="CASCADE"),
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("posts.id", name="fk_collection_items_post_id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_collection_items_post", "post_id"),
        # Khoá sắp của con trỏ listItems (6.4-B dòng 440).
        Index(
            "ix_collection_items_cursor",
            "collection_id",
            text("added_at DESC"),
            text("post_id DESC"),
        ),
    )
