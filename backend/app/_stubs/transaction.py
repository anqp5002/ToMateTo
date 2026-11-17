"""STUB điểm nối 4 — vai BE (`TransactionManager`) sẽ thay.

Một ranh giới giao dịch cho một use case (DOC 6.1-A BE §5.7): chạy callback,
commit, rồi mới chạy các việc `after_commit`; rollback thì bỏ hết việc sau commit.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeVar

T = TypeVar("T")


class SessionLike(Protocol):
    """Phần `Session` mà bản giả này cần; `Session` thật thỏa mãn cấu trúc."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class TransactionManager:
    """Bọc một callback trong transaction và giữ danh sách việc chạy sau commit."""

    def __init__(self, session: SessionLike) -> None:
        self._session = session
        self._after_commit: list[Callable[[], None]] = []

    def run(self, callback: Callable[[], T]) -> T:
        """Chạy `callback`; commit khi thành công, rollback và ném lại khi lỗi."""
        try:
            result = callback()
            self._session.commit()
        except BaseException:
            self._session.rollback()
            self._after_commit.clear()
            raise

        pending, self._after_commit = self._after_commit, []
        for task in pending:
            task()
        return result

    def after_commit(self, callback: Callable[[], None]) -> None:
        """Đăng ký việc chạy sau commit; bị bỏ nếu transaction rollback."""
        self._after_commit.append(callback)
