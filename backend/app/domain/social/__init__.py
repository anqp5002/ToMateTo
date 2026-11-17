"""Thực thể nhóm 4.3 (social) — ánh xạ DDL 6.4-B, không đổi schema.

`_reference_tables` khai báo bảng đích của khoá ngoại (`users`, `posts`) vì S8
chưa có thực thể ORM cho T01/T09; import ở đây để mọi import thực thể social đều
resolve được FK.
"""

from app.domain.social import _reference_tables as _reference_tables  # noqa: F401
