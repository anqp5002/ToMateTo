"""Identity values shared by policies, resolvers and services (DOC 6.1-A §5.7)."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: int
    jti: UUID
    version: int


@dataclass(frozen=True, slots=True)
class SessionClaims:
    subject: int
    jti: UUID
    version: int
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SessionToken:
    raw: str = field(repr=False)
    jti: UUID
    expires_at: datetime
