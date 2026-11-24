"""The sole JWT encoder/decoder; database checks belong to IdentityService."""

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app._stubs.clock import Clock
from app._stubs.errors import UNAUTHENTICATED, AuthorizationError
from app.business.identity.config import IdentityConfig
from app.domain.identity.user import User
from app.domain.value.principal import SessionClaims, SessionToken


def unauthenticated() -> AuthorizationError:
    return AuthorizationError("Phiên đăng nhập không hợp lệ hoặc đã hết hạn.", code=UNAUTHENTICATED)


class SessionTokenService:
    def __init__(self, config: IdentityConfig, clock: Clock) -> None:
        self._config = config
        self._clock = clock

    def issue(self, user: User) -> SessionToken:
        issued_at = self._clock.now().astimezone(UTC).replace(microsecond=0)
        expires_at = issued_at + timedelta(days=7)
        jti = uuid4()
        raw = jwt.encode(
            {
                "sub": str(user.id),
                "jti": str(jti),
                "ver": user.token_version,
                "iat": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
            },
            self._config.jwt_secret,
            algorithm="HS256",
        )
        return SessionToken(raw, jti, expires_at)

    def parse(self, raw: str) -> SessionClaims:
        try:
            if len(raw.encode("utf-8")) >= 1024:
                raise ValueError("Oversized token")
            payload = jwt.decode(
                raw,
                self._config.jwt_secret,
                algorithms=["HS256"],
                options={
                    "require": ["sub", "jti", "ver", "iat", "exp"],
                    # Validate NumericDates against the injected Clock, not the wall clock.
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                },
            )
            if set(payload) != {"sub", "jti", "ver", "iat", "exp"}:
                raise ValueError("Unexpected claims")
            sub, jti, ver, iat, exp = (payload[k] for k in ("sub", "jti", "ver", "iat", "exp"))
            if not isinstance(sub, str) or re.fullmatch(r"[1-9][0-9]*", sub) is None:
                raise ValueError("Invalid subject")
            if int(sub) > 9_223_372_036_854_775_807:
                raise ValueError("Subject exceeds database ID range")
            if not isinstance(jti, str):
                raise ValueError("Invalid jti")
            session_id = UUID(jti)
            if session_id.version != 4 or str(session_id) != jti:
                raise ValueError("Invalid jti")
            if type(ver) is not int or ver < 0 or type(iat) is not int or type(exp) is not int:
                raise ValueError("Invalid numeric claim")
            now = int(self._clock.now().timestamp())
            if iat > now or exp <= now or exp - iat != 7 * 24 * 60 * 60:
                raise ValueError("Invalid lifetime")
            return SessionClaims(
                int(sub),
                session_id,
                ver,
                datetime.fromtimestamp(iat, UTC),
                datetime.fromtimestamp(exp, UTC),
            )
        except (jwt.InvalidTokenError, ValueError, OverflowError, OSError):
            raise unauthenticated() from None
