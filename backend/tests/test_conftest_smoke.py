"""Kiểm conftest: DDL trích đúng bảng, dữ liệu test bị rollback giữa các test."""

from __future__ import annotations

from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from tests.support.ddl import REQUIRED_TABLES, ddl_statements
from tests.support.factories import insert_post, insert_user

ROLLBACK_PROBE_EMAIL = "rollback-probe@example.invalid"


def test_ddl_trich_du_bang_va_khong_sua_ddl() -> None:
    statements = ddl_statements()

    creates = [item for item in statements if item.startswith("CREATE TABLE")]
    assert len(creates) == len(REQUIRED_TABLES)
    table_names = {item.split()[2].strip() for item in creates}
    assert table_names == set(REQUIRED_TABLES)
    # Không kéo theo bảng ngoài phạm vi hay câu lệnh ALTER trỏ media_assets.
    assert not any("media_assets" in item for item in statements)
    assert not any(item.startswith(("COMMENT ON", "BEGIN", "COMMIT")) for item in statements)


def test_schema_co_du_bang(db_connection: Connection) -> None:
    rows = db_connection.execute(
        text(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )
    ).scalars()

    assert set(REQUIRED_TABLES) <= set(rows)


def test_01_ghi_du_lieu_trong_test(db_session: Session) -> None:
    connection = db_session.connection()
    user_id = insert_user(connection, email=ROLLBACK_PROBE_EMAIL)
    post_id = insert_post(connection, user_id=user_id, caption="bài kiểm rollback")

    db_session.commit()

    count = db_session.execute(
        text("SELECT count(*) FROM posts WHERE id = :id"), {"id": post_id}
    ).scalar_one()
    assert count == 1


def test_02_du_lieu_test_truoc_da_bi_rollback(db_session: Session) -> None:
    users = db_session.execute(
        text("SELECT count(*) FROM users WHERE email_normalized = :email"),
        {"email": ROLLBACK_PROBE_EMAIL},
    ).scalar_one()
    posts = db_session.execute(
        text("SELECT count(*) FROM posts WHERE caption = :caption"),
        {"caption": "bài kiểm rollback"},
    ).scalar_one()

    assert users == 0
    assert posts == 0
