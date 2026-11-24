"""Thực thể nhóm 4.3 (social) — ánh xạ DDL 6.4-B, không đổi schema.

`_reference_tables` dùng thực thể User của nhóm Identity và bảng tham chiếu
Post để mọi import thực thể social đều resolve được FK.
"""

from app.domain.social import _reference_tables as _reference_tables  # noqa: F401
