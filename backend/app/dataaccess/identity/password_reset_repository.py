"""T02 storage and atomic single-use grant consumption."""

from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.domain.identity.password_reset import PasswordReset
from app.domain.identity.user import User


class PasswordResetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, request: PasswordReset) -> None:
        self.save(request)

    def save(self, request: PasswordReset) -> None:
        self._session.add(request)
        self._session.flush()

    def find_latest_by_email(self, email: str, for_update: bool = False) -> PasswordReset | None:
        statement = (
            select(PasswordReset)
            .join(User, User.id == PasswordReset.user_id)
            .where(User.email_normalized == email.strip().casefold())
            .order_by(PasswordReset.created_at.desc(), PasswordReset.id.desc())
            .limit(1)
            .execution_options(populate_existing=True)
        )
        if for_update:
            statement = statement.with_for_update(of=PasswordReset)
        return self._session.scalar(statement)

    def find_by_grant_hash(self, grant_hash: str) -> PasswordReset | None:
        return self._session.scalar(
            select(PasswordReset).where(PasswordReset.reset_token_hash == grant_hash)
        )

    def invalidate_open_for_user(self, user_id: int, now: datetime) -> int:
        ids = self._session.scalars(
            update(PasswordReset)
            .where(
                PasswordReset.user_id == user_id,
                PasswordReset.invalidated_at.is_(None),
                PasswordReset.consumed_at.is_(None),
            )
            .values(invalidated_at=now)
            .returning(PasswordReset.id)
        )
        return len(list(ids))

    def consume(self, request_id: int, grant_hash: str, now: datetime) -> bool:
        """Compare-and-set prevents a reset grant being consumed twice."""
        consumed = self._session.scalar(
            update(PasswordReset)
            .where(
                PasswordReset.id == request_id,
                PasswordReset.reset_token_hash == grant_hash,
                PasswordReset.verified_at.is_not(None),
                PasswordReset.invalidated_at.is_(None),
                PasswordReset.consumed_at.is_(None),
                PasswordReset.reset_expires_at > now,
            )
            .values(consumed_at=now)
            .returning(PasswordReset.id)
        )
        return consumed is not None

    def purge_expired(self, now: datetime) -> int:
        expired = self._session.scalars(
            delete(PasswordReset)
            .where(
                or_(
                    PasswordReset.invalidated_at.is_not(None),
                    PasswordReset.consumed_at.is_not(None),
                    (PasswordReset.verified_at.is_(None)) & (PasswordReset.otp_expires_at <= now),
                    PasswordReset.reset_expires_at <= now,
                )
            )
            .returning(PasswordReset.id)
        )
        return len(list(expired))
