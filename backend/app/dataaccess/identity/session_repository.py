"""T03 idempotent revocation and expiry cleanup."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.identity.revoked_token import RevokedToken


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def revoke(self, jti: UUID, user_id: int, expires_at: datetime) -> None:
        self._session.execute(
            insert(RevokedToken)
            .values(jti=jti, user_id=user_id, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=[RevokedToken.jti])
        )

    def is_revoked(self, jti: UUID) -> bool:
        return (
            self._session.scalar(select(RevokedToken.jti).where(RevokedToken.jti == jti))
            is not None
        )

    def prune(self, now: datetime) -> int:
        ids = self._session.scalars(
            delete(RevokedToken).where(RevokedToken.expires_at <= now).returning(RevokedToken.jti)
        )
        return len(list(ids))
