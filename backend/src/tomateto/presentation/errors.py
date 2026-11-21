"""Map service errors to GraphQL extensions or the HTTP upload contract."""

from typing import Any

from graphql import GraphQLError

from tomateto.shared.exceptions import DomainError, SystemError


class ErrorMapper:
    _http_status = {
        "VALIDATION_FAILED": 400,
        "UNAUTHENTICATED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "NOT_AVAILABLE": 404,
        "ALREADY_EXISTS": 409,
        "CONFLICT": 409,
        "RATE_LIMITED": 429,
        "INTEGRATION_UNAVAILABLE": 503,
        "INTERNAL_ERROR": 500,
        "PAYLOAD_TOO_LARGE": 413,
        "UNSUPPORTED_MEDIA_TYPE": 415,
    }

    def to_graphql_error(self, error: Exception) -> GraphQLError:
        safe = self._safe_error(error)
        return GraphQLError(safe.safe_message, extensions=self._extensions(safe))

    def to_http_status(self, error: Exception) -> int:
        return self._http_status[self._safe_error(error).code]

    def to_http_body(self, error: Exception) -> dict[str, dict[str, Any]]:
        safe = self._safe_error(error)
        return {"error": {"message": safe.safe_message, **self._extensions(safe)}}

    @staticmethod
    def _safe_error(error: Exception) -> DomainError:
        return error if isinstance(error, DomainError) else SystemError()

    @staticmethod
    def _extensions(error: DomainError) -> dict[str, Any]:
        result: dict[str, Any] = {"code": error.code}
        if error.field_errors:
            result["fieldErrors"] = [field.as_dict() for field in error.field_errors]
        if error.retry_after_seconds is not None:
            result["retryAfterSeconds"] = error.retry_after_seconds
        return result
