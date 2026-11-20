import pytest
from app.core.clock import Clock
from app.core.config import Config
from app.core.container import AppContainer
from app.core.exceptions import AuthorizationError
from app.core.identity import Principal, SessionVerifier
from app.graphql.context import ContextFactory
from sqlalchemy.orm import Session
from starlette.requests import Request


class IdentityVerifierFake:
    def verify_session(self, raw_token: str) -> Principal:
        principals = {"user-a": Principal(1, "jti-a", 2), "user-b": Principal(2, "jti-b", 3)}
        if raw_token not in principals:
            raise AuthorizationError("UNAUTHENTICATED")
        return principals[raw_token]


def _container() -> AppContainer:
    def factory(session: Session) -> SessionVerifier:
        return IdentityVerifierFake()

    return AppContainer(
        Config("postgresql+psycopg://localhost/test", "fixture"),
        session_factory=Session,
        session_verifier_factory=factory,
    )


@pytest.mark.parametrize(("token", "user_id"), [(None, None), ("user-a", 1), ("user-b", 2)])
def test_tc_be_n0701_identity_is_supplied_by_verifier(
    token: str | None, user_id: int | None
) -> None:
    headers = [] if token is None else [(b"authorization", f"Bearer {token}".encode())]
    request = Request({"type": "http", "headers": headers})
    container = _container()
    with container.new_scope() as scope:
        context = ContextFactory(Clock()).build(request, scope)
        assert (context.principal.user_id if context.principal else None) == user_id


@pytest.mark.parametrize("token", ["bad-signature", "expired", "revoked-jti", "old-version"])
def test_invalid_token_is_rejected_via_identity_port(token: str) -> None:
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    with _container().new_scope() as scope:
        with pytest.raises(AuthorizationError) as error:
            ContextFactory(Clock()).build(request, scope)
        assert error.value.code == "UNAUTHENTICATED"


def test_supplied_token_fails_closed_without_identity_implementation() -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer made-up-token")]})
    with container.new_scope() as scope:
        with pytest.raises(AuthorizationError):
            ContextFactory(Clock()).build(request, scope)


def test_request_and_worker_scopes_do_not_share_sessions() -> None:
    with _container().new_scope() as first, _container().new_scope() as second:
        with _container().new_worker_scope() as worker:
            assert first.session is not second.session
            assert first.session is not worker.session
