"""Test `NotificationRepository` trên PostgreSQL thật (T17, SPEC S8 r2 §4).

Phủ: con trỏ `(created_at DESC, id DESC)` khi nhiều thông báo cùng giây,
`unreadCount` toàn hộp không phụ thuộc trang, `markRead`/`markAllRead` chỉ của
chủ, và CHECK `type`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app._stubs.pagination import PageRequest
from app.dataaccess.social.notification_repository import NotificationRepository
from app.domain.social.notification import Notification, NotificationType
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_post, insert_user

BASE_TIME = datetime(2026, 11, 17, 8, 0, 0, tzinfo=UTC)


def _save(
    session: Session,
    repository: NotificationRepository,
    user_id: int,
    *,
    created_at: datetime,
    kind: NotificationType = NotificationType.LIKE,
    actor_id: int | None = None,
    post_id: int | None = None,
    read_at: datetime | None = None,
) -> Notification:
    """Tạo thông báo với `created_at` chỉ định để kiểm thứ tự cùng giây."""
    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        post_id=post_id,
        type=kind,
        created_at=created_at,
        read_at=read_at,
    )
    return repository.save(notification)


def test_trang_dung_con_tro_kep_khi_cung_giay_khong_trung_khong_sot(
    db_session: Session,
) -> None:
    """Ba thông báo cùng `created_at` vẫn đi hết qua các trang, không lặp/mất."""
    connection = db_session.connection()
    owner = insert_user(connection)
    repository = NotificationRepository(db_session)
    same_second = BASE_TIME
    expected = [_save(db_session, repository, owner, created_at=same_second).id for _ in range(3)]
    # Mới nhất và cũ nhất, để con trỏ phải vượt qua cụm cùng giây ở giữa.
    expected.append(
        _save(db_session, repository, owner, created_at=same_second + timedelta(seconds=1)).id
    )
    expected.append(
        _save(db_session, repository, owner, created_at=same_second - timedelta(seconds=1)).id
    )

    collected: list[int] = []
    cursor: str | None = None
    for _ in range(10):
        page = repository.list_by_user(owner, PageRequest(first=2, after=cursor))
        collected.extend(item.id for item in page.items)
        if not page.has_next_page:
            assert page.end_cursor is None
            break
        cursor = page.end_cursor
        assert cursor is not None
    else:  # pragma: no cover - chặn vòng lặp vô hạn nếu cursor sai
        pytest.fail("Con trỏ không kết thúc sau 10 trang")

    assert len(collected) == len(set(collected))
    assert set(collected) == set(expected)
    # Trang 1: bài mới nhất (t+1) rồi tới bản ghi cuối của cụm cùng giây (id lớn nhất).
    assert collected[:2] == [expected[3], expected[2]]


def test_unread_count_toan_hop_khong_phu_thuoc_trang(db_session: Session) -> None:
    """Trang chỉ có 2 dòng nhưng `unreadCount` vẫn đếm cả 3 thông báo chưa đọc."""
    connection = db_session.connection()
    owner = insert_user(connection)
    other = insert_user(connection)
    repository = NotificationRepository(db_session)
    read_at = BASE_TIME + timedelta(minutes=5)
    for index in range(3):
        _save(db_session, repository, owner, created_at=BASE_TIME + timedelta(seconds=index))
    for index in range(2):
        _save(
            db_session,
            repository,
            owner,
            created_at=BASE_TIME + timedelta(seconds=10 + index),
            read_at=read_at,
        )
    # Thông báo của người khác không được đếm vào hộp của `owner`.
    _save(db_session, repository, other, created_at=BASE_TIME)

    first_page = repository.list_by_user(owner, PageRequest(first=2))

    assert len(first_page.items) == 2
    assert first_page.has_next_page is True
    assert repository.unread_count(owner) == 3
    assert repository.unread_count(other) == 1
    # Trang đầu là hai thông báo mới nhất (đã đọc), không phải ba cái chưa đọc.
    assert all(item.read_at is not None for item in first_page.items)


def test_mark_read_chi_cua_chu_va_idempotent(db_session: Session) -> None:
    """Người khác gọi `mark_read` không đổi dòng nào; chủ đọc lần hai trả 0."""
    connection = db_session.connection()
    owner = insert_user(connection)
    stranger = insert_user(connection)
    repository = NotificationRepository(db_session)
    notification = _save(db_session, repository, owner, created_at=BASE_TIME)

    assert repository.mark_read(notification.id, stranger) == 0
    assert repository.is_unread_by(notification.id, owner) is True

    assert repository.mark_read(notification.id, owner) == 1
    assert repository.is_unread_by(notification.id, owner) is False
    assert repository.mark_read(notification.id, owner) == 0


def test_mark_all_read_chi_hop_cua_chu(db_session: Session) -> None:
    """`mark_all_read` không chạm hộp của người khác."""
    connection = db_session.connection()
    owner = insert_user(connection)
    other = insert_user(connection)
    repository = NotificationRepository(db_session)
    for index in range(2):
        _save(db_session, repository, owner, created_at=BASE_TIME + timedelta(seconds=index))
    other_notification = _save(db_session, repository, other, created_at=BASE_TIME)

    assert repository.mark_all_read(owner) == 2
    assert repository.unread_count(owner) == 0
    assert repository.is_unread_by(other_notification.id, other) is True


def test_find_recipient_id(db_session: Session) -> None:
    """Trả chủ thông báo; mã không tồn tại → None."""
    connection = db_session.connection()
    owner = insert_user(connection)
    repository = NotificationRepository(db_session)
    notification = _save(db_session, repository, owner, created_at=BASE_TIME)

    assert repository.find_recipient_id(notification.id) == owner
    assert repository.find_recipient_id(notification.id + 1_000_000) is None


def test_check_type_chan_loai_ngoai_like_save_follow(db_session: Session) -> None:
    """CHECK `ck_notifications_type` của DDL chặn loại khác."""
    connection = db_session.connection()
    owner = insert_user(connection)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text("INSERT INTO notifications (user_id, type) VALUES (:user_id, 'COMMENT')"),
            {"user_id": owner},
        )
        db_session.flush()
    db_session.rollback()


def test_fk_bai_bi_xoa_thi_post_id_ve_null_con_thong_bao(db_session: Session) -> None:
    """Thông báo gắn bài: xoá bài → `post_id` NULL, dòng thông báo còn."""
    connection = db_session.connection()
    owner = insert_user(connection)
    actor = insert_user(connection)
    post_id = insert_post(connection, user_id=owner)
    repository = NotificationRepository(db_session)
    notification = _save(
        db_session,
        repository,
        owner,
        created_at=BASE_TIME,
        kind=NotificationType.SAVE,
        actor_id=actor,
        post_id=post_id,
    )

    db_session.execute(text("DELETE FROM posts WHERE id = :id"), {"id": post_id})
    db_session.expire(notification)

    assert notification.post_id is None
    assert notification.actor_id == actor
    assert notification.type is NotificationType.SAVE
