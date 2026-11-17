"""Bảng tham chiếu tối thiểu cho khoá ngoại của nhóm social.

S8 r2 **không** có thực thể ORM cho T01 `users` và T09 `posts` (SPEC §2 chỉ giao
T12–T17, T25). Nhưng `mapped_column(ForeignKey("users.id"))` vẫn cần bảng đích
có trong `Base.metadata` thì SQLAlchemy mới resolve được khoá ngoại lúc flush.

Tệp này khai báo đúng các cột mà nhóm social cần đọc/chiếu — **không** dựng
schema (schema đến từ DDL 6.4-B trong `tests/support/ddl.py`):

- `users(id)`: đích của FK `user_id`/`follower_id`/`reporter_id`/`blocker_id`.
- `posts(id, user_id, is_hidden)`: đích của FK `post_id`, kèm hai cột dùng để
  lọc bài ẩn và bài của người bị chặn.

Khi vai DB/BE giao thực thể thật cho `users`/`posts`, xoá tệp này và đổi import:
bảng thật đã có trong cùng `Base.metadata` nên khoá ngoại tự resolve.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Table

from app.domain.base import Base

#: T01 `users` — chỉ cột `id` (khoá ngoại của mọi bảng social).
users_table: Table = Table(
    "users",
    Base.metadata,
    Column("id", BigInteger, primary_key=True),
    extend_existing=True,
)

#: T09 `posts` — cột cần cho FK và cho bộ lọc hiển thị/chặn.
posts_table: Table = Table(
    "posts",
    Base.metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger, nullable=False),
    Column("is_hidden", Boolean, nullable=False, server_default="false"),
    extend_existing=True,
)
