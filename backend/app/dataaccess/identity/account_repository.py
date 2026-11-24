"""T01 lookups include inactive users so the service can check activation."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.identity.user import User


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, user_id: int, for_update: bool = False) -> User | None:
        statement = select(User).where(User.id == user_id).execution_options(populate_existing=True)
        if for_update:
            statement = statement.with_for_update()
        return self._session.scalar(statement)

    def find_by_email(self, email: str) -> User | None:
        return self._session.scalar(
            select(User).where(User.email_normalized == email.strip().casefold())
        )

    def save(self, user: User) -> None:
        self._session.add(user)
        self._session.flush()

    def update_password(self, user_id: int, password_hash: str) -> None:
        """Recovery also calls bump_token_version in the same transaction."""
        self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash, updated_at=func.now())
        )

    def get_token_version(self, user_id: int) -> int | None:
        return self._session.scalar(select(User.token_version).where(User.id == user_id))

    def bump_token_version(self, user_id: int) -> int | None:
        return self._session.scalar(
            update(User)
            .where(User.id == user_id)
            .values(token_version=User.token_version + 1, updated_at=func.now())
            .returning(User.token_version)
        )
