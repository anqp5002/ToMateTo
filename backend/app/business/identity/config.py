"""Required, immutable identity settings; secrets never have defaults."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IdentityConfig:
    jwt_secret: str = field(repr=False)
    otp_pepper: str = field(repr=False)
    jwt_algorithm: str = "HS256"
    jwt_ttl_days: int = 7

    def __post_init__(self) -> None:
        if len(self.jwt_secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes.")
        if not self.otp_pepper.strip():
            raise ValueError("OTP_PEPPER is required.")
        if self.jwt_algorithm != "HS256" or self.jwt_ttl_days != 7:
            raise ValueError("Session policy requires HS256 and a 7-day lifetime.")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "IdentityConfig":
        values = os.environ if env is None else env
        return cls(
            jwt_secret=values.get("JWT_SECRET", ""),
            otp_pepper=values.get("OTP_PEPPER", ""),
            jwt_algorithm=values.get("JWT_ALGORITHM", "HS256"),
            jwt_ttl_days=int(values.get("JWT_TTL_DAYS", "7")),
        )
