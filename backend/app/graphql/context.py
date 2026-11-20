"""Request identity is obtained from the Identity group's verifier port."""

import logging
from typing import TYPE_CHECKING

from starlette.requests import Request
from strawberry.fastapi import BaseContext

from app.core.clock import Clock
from app.core.exceptions import AuthorizationError
from app.core.identity import Principal

if TYPE_CHECKING:
    from app.core.container import RequestScope


logger = logging.getLogger(__name__)


class RequestContext(BaseContext):
    def __init__(self, principal: Principal | None, scope: "RequestScope", clock: Clock) -> None:
        super().__init__()
        self.principal = principal
        self.scope = scope
        self.clock = clock


class ContextFactory:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def build(self, request: Request, scope: "RequestScope") -> RequestContext:
        authorization = request.headers.get("Authorization")
        principal = None
        if authorization is not None:
            try:
                parts = authorization.split()
                if len(parts) != 2 or parts[0].lower() != "bearer":
                    raise AuthorizationError("UNAUTHENTICATED")
                principal = scope.session_verifier.verify_session(parts[1])
            except AuthorizationError as error:
                if error.code == "UNAUTHENTICATED":
                    logger.info(
                        "session_rejected",
                        extra={
                            "detail_code": "SESSION_INVALID",
                            "request_id": getattr(request.state, "request_id", None),
                        },
                    )
                raise
        return RequestContext(principal, scope, self.clock)
