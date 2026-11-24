"""TC-BE-0207..0209/0407..0408: verify order, guest context and handoff port."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from app._stubs.clock import FixedClock
from app._stubs.errors import AuthorizationError
from app.business.identity.config import IdentityConfig
from app.business.identity.identity_service import IdentityService
from app.business.identity.session_token_service import SessionTokenService
from app.domain.identity.user import User
from app.presentation.graphql.context import ContextFactory, SessionVerifier, require_principal
from starlette.requests import Request

from tests.fakes.fake_session_verifier import FakeSessionVerifier


class AccountSpy:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.calls = 0

    def find_by_id(self, user_id: int, for_update: bool = False) -> User | None:
        self.calls += 1
        return self.user


class SessionSpy:
    def __init__(self, revoked: bool = False) -> None:
        self.revoked = revoked
        self.calls = 0

    def is_revoked(self, jti: UUID) -> bool:
        self.calls += 1
        return self.revoked

    def revoke(self, jti: UUID, user_id: int, expires_at: datetime) -> None:
        self.revoked = True


@dataclass
class Scope:
    session_verifier: SessionVerifier


def request(header: str | None) -> Request:
    return Request(
        {"type": "http", "headers": [] if header is None else [(b"authorization", header.encode())]}
    )


def test_tc_be_0207_verified_principal(tokens: SessionTokenService, clock: FixedClock) -> None:
    user = User(id=1, token_version=0, is_active=True)
    accounts, sessions = AccountSpy(user), SessionSpy()
    service = IdentityService(accounts, sessions, tokens)
    token = tokens.issue(user)
    context = ContextFactory(clock).build(request(f"Bearer {token.raw}"), Scope(service))
    principal = require_principal(context)
    assert (principal.user_id, principal.jti, principal.version) == (1, token.jti, 0)
    assert accounts.calls == sessions.calls == 1
    assert not hasattr(principal, "password_hash")


def test_tc_be_0207_no_token_is_guest(clock: FixedClock) -> None:
    context = ContextFactory(clock).build(request(None), Scope(FakeSessionVerifier()))
    assert context.principal is None
    with pytest.raises(AuthorizationError) as error:
        require_principal(context)
    assert error.value.code == "UNAUTHENTICATED"


@pytest.mark.parametrize("header", ["", "Basic test-1", "Bearer", "Bearer test-1 extra"])
def test_bad_header_rejected(header: str, clock: FixedClock) -> None:
    with pytest.raises(AuthorizationError):
        ContextFactory(clock).build(request(header), Scope(FakeSessionVerifier()))


def test_tc_be_0208_invalid_signature_skips_database(tokens: SessionTokenService) -> None:
    accounts, sessions = AccountSpy(None), SessionSpy()
    with pytest.raises(AuthorizationError):
        IdentityService(accounts, sessions, tokens).verify_session("bad.token.signature")
    assert accounts.calls == sessions.calls == 0


def test_tc_be_0209_expired_skips_database(
    tokens: SessionTokenService, identity_config: IdentityConfig, clock: FixedClock
) -> None:
    raw = tokens.issue(User(id=1, token_version=0)).raw
    late_tokens = SessionTokenService(identity_config, FixedClock(clock.now() + timedelta(days=7)))
    accounts, sessions = AccountSpy(None), SessionSpy()
    with pytest.raises(AuthorizationError):
        IdentityService(accounts, sessions, late_tokens).verify_session(raw)
    assert accounts.calls == sessions.calls == 0


def test_tc_be_0407_revoked_stops_before_account(tokens: SessionTokenService) -> None:
    user = User(id=1, token_version=0, is_active=True)
    accounts, sessions = AccountSpy(user), SessionSpy(revoked=True)
    service = IdentityService(accounts, sessions, tokens)
    raw = tokens.issue(user).raw
    with pytest.raises(AuthorizationError):
        service.verify_session(raw)
    assert sessions.calls == 1 and accounts.calls == 0
    assert service.parse_session(raw).subject == 1  # logout can revoke idempotently


@pytest.mark.parametrize("state", ["missing", "changed_version", "inactive"])
def test_tc_be_0408_account_rejected(state: str, tokens: SessionTokenService) -> None:
    original = User(id=1, token_version=0, is_active=True)
    current = (
        None
        if state == "missing"
        else User(
            id=1,
            token_version=1 if state == "changed_version" else 0,
            is_active=state != "inactive",
        )
    )
    accounts, sessions = AccountSpy(current), SessionSpy()
    with pytest.raises(AuthorizationError) as error:
        IdentityService(accounts, sessions, tokens).verify_session(tokens.issue(original).raw)
    assert error.value.field_errors == ()
    assert accounts.calls == sessions.calls == 1


def test_fake_is_explicit_and_rejects_other_values(clock: FixedClock) -> None:
    context = ContextFactory(clock).build(request("bearer test-1"), Scope(FakeSessionVerifier()))
    assert require_principal(context).user_id == 1
    with pytest.raises(AuthorizationError):
        FakeSessionVerifier().verify_session("test-2")
