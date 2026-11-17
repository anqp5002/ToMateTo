"""STUB điểm nối 1 — vai FE (`IdentityService.verifySession`) sẽ thay.

`Principal` và `SessionClaims` giữ đúng chữ ký DOC 6.1-A BE §5.7 (Python
snake_case). Chỉ dựng `Principal` từ token đã xác thực, không từ tham số client.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Principal:
    """Chủ thể đã xác thực của một request."""

    user_id: int
    jti: UUID
    version: int


@dataclass(frozen=True, slots=True)
class SessionClaims:
    """Kết quả giải mã token phiên (trước khi kiểm phiên bản/thu hồi)."""

    subject: int
    jti: UUID
    version: int
    issued_at: datetime
    expires_at: datetime
