"""`like_repository` — đọc/ghi T12 `likes` (chữ ký 6.1-A BE dòng 725-730).

Bất biến của lớp: **không commit**. Transaction do service/`TransactionManager`
quyết định, nhờ vậy thao tác thích nằm chung transaction với thông báo.

`set_state` trả `changed` để service biết trạng thái có thực sự chuyển hay
không — chỉ khi chuyển mới phát thông báo (5.3-B T12).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.social.like import Like


@dataclass(frozen=True, slots=True)
class LikeCount:
    """Số lượt thích của một bài."""

    post_id: int
    count: int


class LikeRepository:
    """Truy vấn lượt thích; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def set_state(self, user_id: int, post_id: int, liked: bool) -> bool:
        """Bật/tắt lượt thích; trả `True` khi trạng thái thực sự đổi.

        Bật dùng `INSERT … ON CONFLICT DO NOTHING` nên gọi lặp lại là no-op
        (không ném lỗi, không tạo dòng thứ hai). Tắt dùng `DELETE` và đọc
        `rowcount` để biết có dòng nào bị xoá.
        """
        if liked:
            result = self._session.execute(
                insert(Like)
                .values(user_id=user_id, post_id=post_id)
                .on_conflict_do_nothing(index_elements=[Like.user_id, Like.post_id])
                .returning(Like.user_id)
            )
            return result.first() is not None

        removed = self._session.execute(
            delete(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        return bool(removed.rowcount)

    def is_liked(self, user_id: int, post_id: int) -> bool:
        """Người dùng đã thích bài này chưa."""
        return bool(
            self._session.scalar(
                select(exists().where(Like.user_id == user_id, Like.post_id == post_id))
            )
        )

    def count_by_post(self, post_id: int) -> int:
        """Tổng lượt thích của một bài."""
        total = self._session.scalar(
            select(func.count()).select_from(Like).where(Like.post_id == post_id)
        )
        return int(total or 0)

    def counts_by_post(self, post_ids: list[int]) -> dict[int, int]:
        """Số lượt thích cho nhiều bài trong **một** truy vấn (tránh N+1).

        Bài không có lượt thích nào sẽ không có mặt trong dict; người gọi đọc
        bằng `.get(post_id, 0)`.
        """
        if not post_ids:
            return {}
        rows = self._session.execute(
            select(Like.post_id, func.count())
            .where(Like.post_id.in_(post_ids))
            .group_by(Like.post_id)
        ).all()
        return {post_id: int(count) for post_id, count in rows}

    def liked_by_user(self, viewer_id: int | None, post_ids: list[int]) -> set[int]:
        """Tập con `post_ids` mà `viewer_id` đã thích; khách (None) → rỗng."""
        if viewer_id is None or not post_ids:
            return set()
        rows = self._session.execute(
            select(Like.post_id).where(Like.user_id == viewer_id, Like.post_id.in_(post_ids))
        ).all()
        return {post_id for (post_id,) in rows}
