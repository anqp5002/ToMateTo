"""Test `LikeRepository` trên PostgreSQL thật (TC-DB-1301, SPEC S8 r2 §4).

Không SQLite, không mock: fixture `db_session` của P2 dựng schema từ DDL 6.4-B.
"""

from __future__ import annotations

from app.dataaccess.social.like_repository import LikeRepository
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_post, insert_user


def _count_likes(session: Session, post_id: int) -> int:
    total = session.scalar(
        text("SELECT count(*) FROM likes WHERE post_id = :post_id"), {"post_id": post_id}
    )
    return int(total or 0)


def test_tc_db_1301_like_twice_creates_one_row(db_session: Session) -> None:
    """TC-DB-1301: thích trùng không tạo dòng thứ hai, `changed` chỉ đúng lần đầu."""
    connection = db_session.connection()
    author = insert_user(connection)
    liker = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = LikeRepository(db_session)

    assert repository.set_state(liker, post_id, True) is True
    assert repository.set_state(liker, post_id, True) is False

    assert _count_likes(db_session, post_id) == 1
    assert repository.is_liked(liker, post_id) is True
    assert repository.count_by_post(post_id) == 1


def test_tc_db_1301_unlike_twice_reports_changed_once(db_session: Session) -> None:
    """Bỏ thích lần đầu xoá dòng; lần hai là no-op (`changed=False`), `count=0`."""
    connection = db_session.connection()
    author = insert_user(connection)
    liker = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = LikeRepository(db_session)
    repository.set_state(liker, post_id, True)

    assert repository.set_state(liker, post_id, False) is True
    assert repository.set_state(liker, post_id, False) is False
    assert repository.count_by_post(post_id) == 0
    assert repository.is_liked(liker, post_id) is False


def test_counts_and_liked_by_user_are_batched(db_session: Session) -> None:
    """`counts_by_post`/`liked_by_user` trả đúng tập cho nhiều bài một lượt."""
    connection = db_session.connection()
    author = insert_user(connection)
    liker = insert_user(connection)
    other = insert_user(connection)
    posts = [insert_post(connection, user_id=author) for _ in range(3)]
    repository = LikeRepository(db_session)

    repository.set_state(liker, posts[0], True)
    repository.set_state(liker, posts[1], True)
    repository.set_state(other, posts[0], True)

    assert repository.counts_by_post(posts) == {posts[0]: 2, posts[1]: 1}
    assert repository.liked_by_user(liker, posts) == {posts[0], posts[1]}
    assert repository.liked_by_user(None, posts) == set()
    assert repository.counts_by_post([]) == {}


def test_foreign_key_rejects_unknown_post(db_session: Session) -> None:
    """FK `post_id` chặn thích bài không tồn tại (lỗi nổi lên, không nuốt)."""
    connection = db_session.connection()
    liker = insert_user(connection)
    repository = LikeRepository(db_session)

    try:
        repository.set_state(liker, 987_654_321, True)
        db_session.flush()
    except IntegrityError:
        db_session.rollback()
    else:  # pragma: no cover - nếu không ném lỗi thì test phải đỏ
        raise AssertionError("FK post_id phải chặn bài không tồn tại")


def test_pk_is_duplicated_pair_not_surrogate(db_session: Session) -> None:
    """Khoá chính là `(user_id, post_id)`: hai người cùng thích một bài vẫn hợp lệ."""
    connection = db_session.connection()
    author = insert_user(connection)
    first = insert_user(connection)
    second = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = LikeRepository(db_session)

    assert repository.set_state(first, post_id, True) is True
    assert repository.set_state(second, post_id, True) is True
    assert repository.count_by_post(post_id) == 2
