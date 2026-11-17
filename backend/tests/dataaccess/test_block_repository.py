"""Test `BlockRepository` trên PostgreSQL thật (T25, O6: chặn hai chiều).

`list_blocked_user_ids` phải trả cả người mình chặn lẫn người chặn mình, không
trùng, và không lẫn người không liên quan.
"""

from __future__ import annotations

import pytest
from app.dataaccess.social.block_repository import BlockRepository
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_user


def _block(session: Session, blocker_id: int, blocked_id: int) -> None:
    session.execute(
        text("INSERT INTO user_blocks (blocker_id, blocked_id) VALUES (:b, :c)"),
        {"b": blocker_id, "c": blocked_id},
    )
    session.flush()


def test_loc_hai_chieu_khong_trung(db_session: Session) -> None:
    """Viewer thấy cả hai chiều; chặn chéo hai chiều chỉ ra một lần."""
    connection = db_session.connection()
    viewer = insert_user(connection)
    blocked_by_viewer = insert_user(connection)
    blocking_viewer = insert_user(connection)
    mutual = insert_user(connection)
    bystander = insert_user(connection)
    repository = BlockRepository(db_session)

    _block(db_session, viewer, blocked_by_viewer)
    _block(db_session, blocking_viewer, viewer)
    _block(db_session, viewer, mutual)
    _block(db_session, mutual, viewer)
    _block(db_session, bystander, blocked_by_viewer)

    result = repository.list_blocked_user_ids(viewer)

    assert result == sorted([blocked_by_viewer, blocking_viewer, mutual])
    assert len(result) == len(set(result))
    assert bystander not in result


def test_viewer_khong_chan_ai_tra_rong(db_session: Session) -> None:
    """Không có dòng nào liên quan → danh sách rỗng (không phải lỗi)."""
    connection = db_session.connection()
    viewer = insert_user(connection)
    other = insert_user(connection)
    _block(db_session, other, insert_user(connection))

    assert BlockRepository(db_session).list_blocked_user_ids(viewer) == []


def test_pk_doi_chan_trung_khong_tao_dong_thu_hai(db_session: Session) -> None:
    """PK `(blocker_id, blocked_id)` giữ đúng một dòng khi chèn lặp."""
    connection = db_session.connection()
    blocker = insert_user(connection)
    blocked = insert_user(connection)
    _block(db_session, blocker, blocked)

    with pytest.raises(IntegrityError):
        _block(db_session, blocker, blocked)
    db_session.rollback()


def test_check_khong_tu_chan(db_session: Session) -> None:
    """CHECK `ck_user_blocks_not_self` chặn tự chặn."""
    connection = db_session.connection()
    user = insert_user(connection)

    with pytest.raises(IntegrityError):
        _block(db_session, user, user)
    db_session.rollback()
