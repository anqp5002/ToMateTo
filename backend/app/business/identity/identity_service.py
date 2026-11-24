"""B1 session verification: signature/expiry → revocation → version → active."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.business.identity.session_token_service import SessionTokenService, unauthenticated
from app.domain.identity.user import User
from app.domain.value.principal import Principal, SessionClaims


class Accounts(Protocol):
    def find_by_id(self, user_id: int, for_update: bool = False) -> User | None: ...


class Sessions(Protocol):
    def is_revoked(self, jti: UUID) -> bool: ...

    def revoke(self, jti: UUID, user_id: int, expires_at: datetime) -> None: ...


class IdentityService:
    def __init__(self, accounts: Accounts, sessions: Sessions, tokens: SessionTokenService) -> None:
        self._accounts = accounts
        self._sessions = sessions
        self._tokens = tokens

    def verify_session(self, raw_token: str) -> Principal:
        claims = self._tokens.parse(raw_token)
        if self._sessions.is_revoked(claims.jti):
            raise unauthenticated()
        account = self._accounts.find_by_id(claims.subject)
        if account is None or account.token_version != claims.version or not account.is_active:
            raise unauthenticated()
        return Principal(account.id, claims.jti, claims.version)

    def parse_session(self, raw_token: str) -> SessionClaims:
        """Logout can parse a revoked token without running verify_session again."""
        return self._tokens.parse(raw_token)

    def revoke_session(self, raw_token: str) -> None:
        """Idempotent token revocation, without requiring the token to be unrevoked."""
        claims = self.parse_session(raw_token)
        self._sessions.revoke(claims.jti, claims.subject, claims.expires_at)
