"""Per-request context. Missing header means guest; invalid header is an error."""

from typing import Protocol

from starlette.requests import Request
from strawberry.fastapi import BaseContext

from app._stubs.clock import Clock
from app.business.identity.session_token_service import unauthenticated
from app.domain.value.principal import Principal


class SessionVerifier(Protocol):
    def verify_session(self, raw_token: str) -> Principal: ...


class RequestScope(Protocol):
    @property
    def session_verifier(self) -> SessionVerifier: ...


class RequestContext(BaseContext):
    def __init__(self, principal: Principal | None, scope: RequestScope, clock: Clock) -> None:
        super().__init__()
        self.principal = principal
        self.scope = scope
        self.clock = clock


class ContextFactory:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def build(self, request: Request, scope: RequestScope) -> RequestContext:
        authorization = request.headers.get("Authorization")
        principal = None
        if authorization is not None:
            parts = authorization.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise unauthenticated()
            principal = scope.session_verifier.verify_session(parts[1])
        return RequestContext(principal, scope, self._clock)


def require_principal(context: RequestContext) -> Principal:
    if context.principal is None:
        raise unauthenticated()
    return context.principal
