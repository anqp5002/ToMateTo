"""Test `FollowRepository` trên PostgreSQL thật (TC-DB-1401, SPEC S8 r2 §4)."""

from __future__ import annotations

from app.dataaccess.social.follow_repository import FollowRepository
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_user


def _count_follows(session: Session) -> int:
    return int(session.scalar(text("SELECT count(*) FROM follows")) or 0)


def test_tc_db_1401_follow_twice_creates_one_row(db_session: Session) -> None:
    """TC-DB-1401: theo dõi trùng không tạo dòng thứ hai."""
    connection = db_session.connection()
    follower = insert_user(connection)
    followee = insert_user(connection)
    repository = FollowRepository(db_session)

    assert repository.set_state(follower, followee, True) is True
    assert repository.set_state(follower, followee, True) is False

    assert _count_follows(db_session) == 1
    assert repository.is_following(follower, followee) is True


def test_tc_db_1401_counts_followers_and_following(db_session: Session) -> None:
    """TC-DB-1401: đếm đúng số người theo dõi và số người đang theo dõi."""
    connection = db_session.connection()
    center = insert_user(connection)
    fans = [insert_user(connection) for _ in range(3)]
    idol = insert_user(connection)
    repository = FollowRepository(db_session)

    for fan in fans:
        repository.set_state(fan, center, True)
    repository.set_state(center, idol, True)
    repository.set_state(center, idol, True)  # lặp lại: không tăng số

    counts = repository.counts(center)
    assert counts.followers == 3
    assert counts.following == 1

    idol_counts = repository.counts(idol)
    assert idol_counts.followers == 1
    assert idol_counts.following == 0


def test_unfollow_twice_reports_changed_once(db_session: Session) -> None:
    """Bỏ theo dõi lần đầu xoá dòng; lần hai `changed=False`, bảng rỗng."""
    connection = db_session.connection()
    follower = insert_user(connection)
    followee = insert_user(connection)
    repository = FollowRepository(db_session)
    repository.set_state(follower, followee, True)

    assert repository.set_state(follower, followee, False) is True
    assert repository.set_state(follower, followee, False) is False
    assert _count_follows(db_session) == 0
    assert repository.is_following(follower, followee) is False


def test_check_constraint_blocks_self_follow(db_session: Session) -> None:
    """CHECK `ck_follows_not_self`: tự theo dõi bị CSDL chặn, lỗi nổi lên."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = FollowRepository(db_session)

    try:
        repository.set_state(user_id, user_id, True)
        db_session.flush()
    except IntegrityError:
        db_session.rollback()
    else:  # pragma: no cover
        raise AssertionError("ck_follows_not_self phải chặn tự theo dõi")


def test_counts_are_zero_for_new_user(db_session: Session) -> None:
    """Tài khoản chưa có quan hệ: cả hai số đều 0 (không NULL)."""
    connection = db_session.connection()
    user_id = insert_user(connection)

    counts = FollowRepository(db_session).counts(user_id)
    assert (counts.followers, counts.following) == (0, 0)
