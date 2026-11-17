"""`notification_repository` — T17 `notifications` (chữ ký 6.1-A BE dòng 695-702).

Hai bất biến:

- **Không commit**: transaction thuộc service/`TransactionManager`.
- Trang dùng con trỏ kép `(created_at DESC, id DESC)`; `unread_count` đếm **toàn
  hộp**, không phụ thuộc trang đang xem (7.1-A.1 Q23).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, exists, func, or_, select, update
from sqlalchemy.orm import Session

from app._stubs.pagination import CursorCodec, PageRequest
from app.domain.social.notification import Notification


@dataclass(frozen=True, slots=True)
class NotificationPage:
    """Một trang hộp thư kèm con trỏ cho trang sau."""

    items: list[Notification]
    end_cursor: str | None
    has_next_page: bool


class NotificationRepository:
    """Truy vấn hộp thư; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: int, page: PageRequest) -> NotificationPage:
        """Trang mới nhất trước, khoá theo `(created_at, id)` để không trùng/sót."""
        statement = select(Notification).where(Notification.user_id == user_id)
        if page.after is not None:
            payload = CursorCodec.decode(page.after)
            statement = statement.where(
                or_(
                    Notification.created_at < payload.created_at,
                    and_(
                        Notification.created_at == payload.created_at,
                        Notification.id < payload.id,
                    ),
                )
            )
        statement = statement.order_by(
            Notification.created_at.desc(), Notification.id.desc()
        ).limit(page.first + 1)
        rows = list(self._session.scalars(statement))
        has_next_page = len(rows) > page.first
        items = rows[: page.first]
        end_cursor = (
            CursorCodec.encode(items[-1].created_at, items[-1].id)
            if has_next_page and items
            else None
        )
        return NotificationPage(items=items, end_cursor=end_cursor, has_next_page=has_next_page)

    def unread_count(self, user_id: int) -> int:
        """Tổng thông báo chưa đọc của **cả hộp**, không giới hạn theo trang."""
        total = self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        return int(total or 0)

    def find_recipient_id(self, notification_id: int) -> int | None:
        """Chủ của thông báo; `None` khi không tồn tại (service tự trả NOT_FOUND)."""
        recipient = self._session.scalar(
            select(Notification.user_id).where(Notification.id == notification_id)
        )
        return None if recipient is None else int(recipient)

    def mark_read(self, notification_id: int, user_id: int) -> int:
        """Đánh dấu một thông báo đã đọc **nếu thuộc `user_id`**; trả số dòng đổi.

        Điều kiện `read_at IS NULL` làm thao tác lặp lại trả `0` thay vì ghi đè
        dấu thời gian cũ.
        """
        result = self._session.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=func.now())
        )
        return int(result.rowcount or 0)

    def mark_all_read(self, user_id: int) -> int:
        """Đánh dấu toàn bộ thông báo chưa đọc của chính `user_id`; trả số dòng đổi."""
        result = self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=func.now())
        )
        return int(result.rowcount or 0)

    def save(self, notification: Notification) -> Notification:
        """Thêm thông báo mới (chưa commit); trả lại chính thực thể đã có `id`."""
        self._session.add(notification)
        self._session.flush()
        self._session.refresh(notification)
        return notification

    def is_unread_by(self, notification_id: int, user_id: int) -> bool:
        """Tiện cho test/service kiểm nhanh trạng thái chưa đọc của chủ."""
        return bool(
            self._session.scalar(
                select(
                    exists().where(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                        Notification.read_at.is_(None),
                    )
                )
            )
        )
