"""Session verification contract implemented by the Identity group."""

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import AuthorizationError


@dataclass(frozen=True)
class Principal:
    user_id: int
    jti: str
    token_version: int


class SessionVerifier(Protocol):
    """B1 checks signature, expiry, revocation and current account version."""

    def verify_session(self, raw_token: str) -> Principal: ...


class UnavailableSessionVerifier:
    """Fail closed until the Identity group's verifier is wired at startup."""

    def verify_session(self, raw_token: str) -> Principal:
        raise AuthorizationError("UNAUTHENTICATED")
