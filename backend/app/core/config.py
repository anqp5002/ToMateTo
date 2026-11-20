"""Immutable process configuration, loaded explicitly at application startup."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    database_url: str = field(repr=False)
    jwt_secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL is required.")
        if not self.jwt_secret.strip():
            raise ValueError("JWT_SECRET is required.")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Config":
        source = os.environ if environ is None else environ
        return cls(source.get("DATABASE_URL", ""), source.get("JWT_SECRET", ""))
