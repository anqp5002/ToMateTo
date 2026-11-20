import pytest
from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    DomainError,
    FieldError,
    IntegrationError,
    NotFoundError,
    SystemError,
    ValidationError,
)
from app.graphql.errors import ErrorMapper


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (ValidationError(), 400),
        (ValidationError("PAYLOAD_TOO_LARGE"), 413),
        (ValidationError("UNSUPPORTED_MEDIA_TYPE"), 415),
        (AuthorizationError("UNAUTHENTICATED"), 401),
        (AuthorizationError("FORBIDDEN"), 403),
        (AuthorizationError("NOT_AVAILABLE"), 404),
        (NotFoundError(), 404),
        (BusinessRuleError("ALREADY_EXISTS"), 409),
        (BusinessRuleError("CONFLICT"), 409),
        (BusinessRuleError("RATE_LIMITED"), 429),
        (IntegrationError(), 503),
        (SystemError(), 500),
    ],
)
def test_error_mapper_preserves_code_and_transport_status(error: DomainError, status: int) -> None:
    mapper = ErrorMapper()
    result = mapper.to_graphql_error(error)
    assert result.extensions is not None
    assert result.extensions["code"] == error.code
    assert mapper.to_http_status(error) == status
    assert mapper.to_http_body(error)["error"]["code"] == error.code


def test_mapper_preserves_field_errors_and_optional_retry() -> None:
    mapper = ErrorMapper()
    error = ValidationError(
        field_errors=[FieldError("page.first", "PAGE_SIZE_INVALID", "Số mục không hợp lệ.")]
    )
    mapped = mapper.to_graphql_error(error)
    assert mapped.extensions is not None
    assert mapped.extensions["fieldErrors"][0]["field"] == "page.first"
    assert "retryAfterSeconds" not in mapped.extensions
    limited = mapper.to_graphql_error(BusinessRuleError("RATE_LIMITED", retry_after_seconds=20))
    assert limited.extensions == {"code": "RATE_LIMITED", "retryAfterSeconds": 20}


def test_unknown_exception_has_safe_public_message() -> None:
    mapped = ErrorMapper().to_graphql_error(RuntimeError("private database details"))
    assert mapped.extensions == {"code": "INTERNAL_ERROR"}
    assert "private" not in mapped.message
