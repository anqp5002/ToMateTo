"""STUB điểm nối 4 — vai BE (`PageRequest`, `CursorCodec`) sẽ thay.

Chỉ đủ cho `NotificationRepository.listByUser` và `CollectionRepository.listItems`
(SPEC S8 r2 §3): `first` 1…50 (thiếu → 10, >50 → 50), con trỏ đục mã hoá cặp
`(created_at, id)` để hai bản ghi cùng giây không trùng/sót.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import UTC, datetime

from app._stubs.errors import FieldError, ValidationError

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


@dataclass(frozen=True, slots=True)
class CursorPayload:
    """Giá trị đã giải mã của một con trỏ."""

    created_at: datetime
    id: int


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Kích thước trang và con trỏ `after` đã chuẩn hoá."""

    first: int = DEFAULT_PAGE_SIZE
    after: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.first <= MAX_PAGE_SIZE:
            raise ValidationError(
                f"Kích thước trang phải từ 1 đến {MAX_PAGE_SIZE}.",
                field_errors=(
                    FieldError(
                        field="page.first",
                        code="PAGE_SIZE_INVALID",
                        message=f"Kích thước trang phải từ 1 đến {MAX_PAGE_SIZE}.",
                    ),
                ),
            )

    @classmethod
    def default(cls) -> PageRequest:
        """Trang mặc định 10 phần tử, không con trỏ."""
        return cls()

    @classmethod
    def from_input(cls, first: int | None, after: str | None = None) -> PageRequest:
        """Áp quy tắc hợp đồng: thiếu → 10, ≤ 0 → VALIDATION_FAILED, > 50 → 50."""
        if first is None:
            size = DEFAULT_PAGE_SIZE
        elif first <= 0:
            raise ValidationError(
                "Kích thước trang phải lớn hơn 0.",
                field_errors=(
                    FieldError(
                        field="page.first",
                        code="PAGE_SIZE_INVALID",
                        message="Kích thước trang phải lớn hơn 0.",
                    ),
                ),
            )
        else:
            size = min(first, MAX_PAGE_SIZE)
        return cls(first=size, after=after or None)


class CursorCodec:
    """Mã hoá/giải mã con trỏ keyset `(created_at, id)` dạng base64url."""

    @staticmethod
    def encode(created_at: datetime, id: int) -> str:
        """Ghép `created_at` UTC (micro giây) và `id` thành chuỗi đục."""
        if created_at.tzinfo is None:
            raise ValueError("created_at phải là thời điểm có múi giờ.")
        if id <= 0:
            raise ValueError("id của con trỏ phải là số dương.")
        instant = created_at.astimezone(UTC).isoformat(timespec="microseconds")
        raw = f"{instant}|{id}".encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @staticmethod
    def decode(cursor: str) -> CursorPayload:
        """Giải mã con trỏ; sai định dạng → `VALIDATION_FAILED · CURSOR_INVALID`."""
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            raw = base64.urlsafe_b64decode(padded.encode()).decode()
            instant_text, id_text = raw.rsplit("|", 1)
            created_at = datetime.fromisoformat(instant_text)
            if created_at.tzinfo is None:
                raise ValueError("con trỏ thiếu múi giờ")
            identifier = int(id_text)
            if identifier <= 0:
                raise ValueError("con trỏ có id không dương")
        except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
            raise ValidationError(
                "Không thể tải trang tiếp. Vui lòng tải lại.",
                field_errors=(
                    FieldError(
                        field="page.after",
                        code="CURSOR_INVALID",
                        message="Con trỏ không hợp lệ hoặc đã hết hiệu lực.",
                    ),
                ),
            ) from exc
        return CursorPayload(created_at=created_at.astimezone(UTC), id=identifier)
