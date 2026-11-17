"""Test `ReportRepository` trên PostgreSQL thật (T16, SPEC S8 r2 §4).

Phủ yêu cầu bắt buộc: xoá bài → `post_id` NULL nhưng `original_post_id` và
`evidence_snapshot` còn nguyên; `original_post_id` không FK nên giữ được mã bài
đã biến mất; `exists_for_user` chặn báo trùng; repository không tự ẩn bài.
"""

from __future__ import annotations

import pytest
from app.dataaccess.social.report_repository import ReportRepository
from app.domain.social.report import Report
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_post, insert_user

SNAPSHOT = {"caption": "ảnh chụp nội dung", "dish": "phở", "author": 1}


def _report(reporter_id: int, post_id: int | None, original_post_id: int) -> Report:
    return Report(
        reporter_id=reporter_id,
        post_id=post_id,
        original_post_id=original_post_id,
        reason="spam",
        evidence_snapshot=dict(SNAPSHOT),
    )


def test_insert_va_exists_for_user(db_session: Session) -> None:
    """Báo cáo mới có `id`, tìm thấy theo `(reporter, original_post)`."""
    connection = db_session.connection()
    reporter = insert_user(connection)
    author = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = ReportRepository(db_session)

    saved = repository.insert(_report(reporter, post_id, post_id))

    assert saved.id > 0
    assert saved.created_at is not None
    assert repository.exists_for_user(reporter, post_id) is True
    assert repository.exists_for_user(author, post_id) is False


def test_xoa_bai_thi_post_id_null_con_nguyen_goc_va_snapshot(db_session: Session) -> None:
    """FK `SET NULL` chỉ cắt liên kết sống; lịch sử báo cáo bất biến."""
    connection = db_session.connection()
    reporter = insert_user(connection)
    author = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = ReportRepository(db_session)
    saved = repository.insert(_report(reporter, post_id, post_id))

    db_session.execute(text("DELETE FROM posts WHERE id = :id"), {"id": post_id})
    db_session.expire(saved)

    assert saved.post_id is None
    assert saved.original_post_id == post_id
    assert saved.evidence_snapshot == SNAPSHOT
    # Báo cáo vẫn còn sau khi bài mất.
    assert repository.exists_for_user(reporter, post_id) is True


def test_original_post_id_khong_co_fk_nen_giu_duoc_ma_bai_da_xoa(db_session: Session) -> None:
    """`original_post_id` không FK: ghi được mã bài chưa/không còn tồn tại."""
    connection = db_session.connection()
    reporter = insert_user(connection)
    repository = ReportRepository(db_session)

    saved = repository.insert(_report(reporter, None, 987_654_321))

    assert saved.post_id is None
    assert saved.original_post_id == 987_654_321


def test_trung_reporter_va_original_post_bi_chan(db_session: Session) -> None:
    """UNIQUE `(reporter_id, original_post_id)` chặn báo cùng bài hai lần."""
    connection = db_session.connection()
    reporter = insert_user(connection)
    repository = ReportRepository(db_session)
    original_post_id = 424_242
    repository.insert(_report(reporter, None, original_post_id))

    with pytest.raises(IntegrityError):
        repository.insert(_report(reporter, None, original_post_id))
    db_session.rollback()


def test_post_id_phai_bang_original_post_id(db_session: Session) -> None:
    """CHECK `ck_reports_original_post`: `post_id` khác mã gốc bị chặn."""
    connection = db_session.connection()
    reporter = insert_user(connection)
    author = insert_user(connection)
    post_id = insert_post(connection, user_id=author)
    repository = ReportRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.insert(_report(reporter, post_id, post_id + 1))
    db_session.rollback()


def test_snapshot_phai_la_json_object(db_session: Session) -> None:
    """CHECK `ck_reports_snapshot` đòi `jsonb_typeof = 'object'`."""
    connection = db_session.connection()
    reporter = insert_user(connection)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO reports (reporter_id, original_post_id, reason, evidence_snapshot)"
                " VALUES (:reporter_id, 7, 'spam', '[]'::jsonb)"
            ),
            {"reporter_id": reporter},
        )
        db_session.flush()
    db_session.rollback()


def test_bang_reports_khong_co_cot_is_hidden(db_session: Session) -> None:
    """Báo cáo không tự ẩn bài: DDL T16 không có `is_hidden`."""
    columns = db_session.execute(
        text("SELECT column_name FROM information_schema.columns" " WHERE table_name = 'reports'")
    ).scalars()

    assert "is_hidden" not in set(columns)
