"""Chèn nhanh dữ liệu tối thiểu bằng SQL cho test CSDL (PostgreSQL thật).

Không dùng ORM để test repository không phụ thuộc model của pane khác; mọi hàm
nhận `Connection` đang mở transaction của test, không commit.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Connection, text

PASSWORD_HASH_FIXTURE = "test-hash-not-a-real-secret"  # noqa: S105 - hash giả cho fixture


def insert_user(
    connection: Connection,
    *,
    email: str | None = None,
    display_name: str = "Người dùng kiểm thử",
    password_hash: str = PASSWORD_HASH_FIXTURE,
    is_active: bool = True,
) -> int:
    """Tạo một user; email mặc định là duy nhất theo UUID."""
    resolved_email = email or f"user-{uuid4().hex}@example.invalid"
    row = connection.execute(
        text(
            "INSERT INTO users (email, email_normalized, password_hash, display_name, is_active)"
            " VALUES (:email, :email, :password_hash, :display_name, :is_active)"
            " RETURNING id"
        ),
        {
            "email": resolved_email,
            "password_hash": password_hash,
            "display_name": display_name,
            "is_active": is_active,
        },
    ).one()
    return int(row[0])


def insert_dish(connection: Connection, *, name: str | None = None) -> int:
    """Tạo một món; `name_normalized` duy nhất theo UUID nên không đụng dữ liệu khác."""
    resolved = name or f"Món kiểm thử {uuid4().hex}"
    row = connection.execute(
        text(
            "INSERT INTO dishes (name, name_normalized, is_seed) VALUES (:name, :normalized, false)"
            " RETURNING id"
        ),
        {"name": resolved, "normalized": resolved.lower()},
    ).one()
    return int(row[0])


def insert_post(
    connection: Connection,
    *,
    user_id: int,
    dish_id: int | None = None,
    caption: str | None = None,
    is_hidden: bool = False,
    created_at: datetime | None = None,
) -> int:
    """Tạo một bài; tự tạo món nếu thiếu `dish_id` (món là FK bắt buộc của T09)."""
    resolved_dish = dish_id if dish_id is not None else insert_dish(connection)
    row = connection.execute(
        text(
            "INSERT INTO posts (user_id, dish_id, caption, is_hidden, created_at, updated_at)"
            " VALUES (:user_id, :dish_id, :caption, :is_hidden,"
            " COALESCE(:created_at, now()), COALESCE(:created_at, now()))"
            " RETURNING id"
        ),
        {
            "user_id": user_id,
            "dish_id": resolved_dish,
            "caption": caption,
            "is_hidden": is_hidden,
            "created_at": created_at or datetime.now(tz=UTC),
        },
    ).one()
    return int(row[0])
