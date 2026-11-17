"""STUB điểm nối 4 — vai BE (ErrorMapper) sẽ thay.

Cây ngoại lệ miền theo DOC 7.2-A §2: một `DomainError` mang mã hợp đồng, thông
điệp an toàn và `field_errors` tùy chọn; sáu lớp con ứng với sáu nhóm lỗi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar, Final

#: Mười mã `extensions.code` của DOC 5.2-A §6.
VALIDATION_FAILED: Final = "VALIDATION_FAILED"
UNAUTHENTICATED: Final = "UNAUTHENTICATED"
FORBIDDEN: Final = "FORBIDDEN"
NOT_FOUND: Final = "NOT_FOUND"
NOT_AVAILABLE: Final = "NOT_AVAILABLE"
ALREADY_EXISTS: Final = "ALREADY_EXISTS"
CONFLICT: Final = "CONFLICT"
RATE_LIMITED: Final = "RATE_LIMITED"
INTEGRATION_UNAVAILABLE: Final = "INTEGRATION_UNAVAILABLE"
INTERNAL_ERROR: Final = "INTERNAL_ERROR"

API_ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        VALIDATION_FAILED,
        UNAUTHENTICATED,
        FORBIDDEN,
        NOT_FOUND,
        NOT_AVAILABLE,
        ALREADY_EXISTS,
        CONFLICT,
        RATE_LIMITED,
        INTEGRATION_UNAVAILABLE,
        INTERNAL_ERROR,
    }
)


@dataclass(frozen=True, slots=True)
class FieldError:
    """Một phần tử `extensions.fieldErrors` (DOC 5.2-A §6)."""

    field: str
    code: str
    message: str


class DomainError(Exception):
    """Lỗi miền gốc; thông điệp phải an toàn để trả cho người dùng."""

    default_code: ClassVar[str] = INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        field_errors: tuple[FieldError, ...] = (),
    ) -> None:
        resolved = code or self.default_code
        if resolved not in API_ERROR_CODES:
            raise ValueError(f"Mã lỗi không thuộc hợp đồng API: {resolved!r}")
        super().__init__(message)
        self.message = message
        self.code = resolved
        self.field_errors = field_errors
        self.timestamp = datetime.now(tz=UTC)


class ValidationError(DomainError):
    """Dữ liệu đầu vào sai; có thể kèm `field_errors`."""

    default_code: ClassVar[str] = VALIDATION_FAILED


class BusinessRuleError(DomainError):
    """Vi phạm quy tắc nghiệp vụ: ALREADY_EXISTS, CONFLICT hoặc RATE_LIMITED."""

    default_code: ClassVar[str] = CONFLICT


class AuthorizationError(DomainError):
    """Thiếu xác thực (UNAUTHENTICATED) hoặc thiếu quyền (FORBIDDEN/NOT_AVAILABLE)."""

    default_code: ClassVar[str] = FORBIDDEN


class NotFoundError(DomainError):
    """Tài nguyên không tồn tại."""

    default_code: ClassVar[str] = NOT_FOUND


class IntegrationError(DomainError):
    """Dịch vụ ngoài không khả dụng."""

    default_code: ClassVar[str] = INTEGRATION_UNAVAILABLE


class SystemError(DomainError):
    """Lỗi nội bộ hoặc lỗi CSDL chưa phân loại."""

    default_code: ClassVar[str] = INTERNAL_ERROR
