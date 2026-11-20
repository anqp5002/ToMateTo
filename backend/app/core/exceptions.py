"""Application errors shared by services and presentation adapters."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass

SAFE_MESSAGES = {
    "VALIDATION_FAILED": "Vui lòng kiểm tra lại dữ liệu đã nhập.",
    "UNAUTHENTICATED": "Phiên đã hết. Vui lòng đăng nhập lại.",
    "FORBIDDEN": "Bạn không có quyền thực hiện thao tác này.",
    "NOT_AVAILABLE": "Nội dung này không còn khả dụng.",
    "NOT_FOUND": "Nội dung này không còn khả dụng.",
    "ALREADY_EXISTS": "Nội dung đã tồn tại.",
    "CONFLICT": "Nội dung đã thay đổi. Vui lòng tải lại.",
    "RATE_LIMITED": "Bạn thao tác quá nhanh. Vui lòng thử lại sau.",
    "INTEGRATION_UNAVAILABLE": "Dịch vụ đang bận. Vui lòng thử lại sau.",
    "INTERNAL_ERROR": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau.",
    "PAYLOAD_TOO_LARGE": "Ảnh vượt 10 MB. Vui lòng chọn ảnh nhỏ hơn.",
    "UNSUPPORTED_MEDIA_TYPE": "Không thể tải ảnh. Vui lòng thử lại.",
}


@dataclass(frozen=True)
class FieldError:
    field: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class DomainError(Exception):
    """Carry only safe client-facing error metadata."""

    default_code = "INTERNAL_ERROR"

    def __init__(
        self,
        code: str | None = None,
        message: str | None = None,
        *,
        field_errors: Sequence[FieldError] = (),
        retry_after_seconds: int | None = None,
    ) -> None:
        self.code = code or self.default_code
        if self.code not in SAFE_MESSAGES:
            raise ValueError("Unknown API error code.")
        if retry_after_seconds is not None and retry_after_seconds < 0:
            raise ValueError("Retry delay must be nonnegative.")
        self.safe_message = message or SAFE_MESSAGES[self.code]
        self.field_errors = tuple(field_errors)
        self.retry_after_seconds = retry_after_seconds
        super().__init__(self.safe_message)


class ValidationError(DomainError):
    default_code = "VALIDATION_FAILED"


class BusinessRuleError(DomainError):
    default_code = "CONFLICT"


class AuthorizationError(DomainError):
    default_code = "FORBIDDEN"


class NotFoundError(DomainError):
    default_code = "NOT_FOUND"


class IntegrationError(DomainError):
    default_code = "INTEGRATION_UNAVAILABLE"


class SystemError(DomainError):
    default_code = "INTERNAL_ERROR"
