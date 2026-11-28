import re
from dataclasses import dataclass, field

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app._stubs.clock import Clock
from app._stubs.errors import (
    ALREADY_EXISTS,
    UNAUTHENTICATED,
    AuthorizationError,
    BusinessRuleError,
    FieldError,
    ValidationError,
)
from app._stubs.transaction import TransactionManager
from app.bootstrap.identity_scope import build_identity_service
from app.business.identity.config import IdentityConfig
from app.business.identity.password_policy import PasswordPolicy
from app.business.identity.session_token_service import SessionTokenService
from app.dataaccess.identity.account_repository import AccountRepository
from app.dataaccess.social.collection_repository import CollectionRepository
from app.domain.identity.user import User

SESSION_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class AuthResult:
    user: User
    token: str = field(repr=False)


def duplicate_email() -> BusinessRuleError:
    message = "Email đã được sử dụng."
    return BusinessRuleError(
        message, code=ALREADY_EXISTS, field_errors=(FieldError("email", "EMAIL_EXISTS", message),)
    )


class AuthService:
    def __init__(
        self, session: Session, config: IdentityConfig, clock: Clock, dummy_hash: str
    ) -> None:
        self.accounts = AccountRepository(session)
        self.collections = CollectionRepository(session)
        self.transaction = TransactionManager(session)
        self.passwords = PasswordPolicy()
        self.tokens = SessionTokenService(config, clock)
        self.identity = build_identity_service(session, config, clock)
        self.dummy_hash = dummy_hash

    def register(self, email: str, password: str, display_name: str) -> AuthResult:
        email, display_name = email.strip(), display_name.strip()
        normalized = email.casefold()
        if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValidationError(
                "Email không hợp lệ.",
                field_errors=(FieldError("email", "EMAIL_INVALID", "Email không hợp lệ."),),
            )
        if not display_name:
            raise ValidationError(
                "Vui lòng nhập tên hiển thị.",
                field_errors=(
                    FieldError("displayName", "REQUIRED", "Vui lòng nhập tên hiển thị."),
                ),
            )
        hashed = self.passwords.hash(password)

        def persist() -> User:
            if self.accounts.find_by_email(normalized) is not None:
                raise duplicate_email()
            user = User(
                email=email,
                email_normalized=normalized,
                display_name=display_name,
                password_hash=hashed,
            )
            self.accounts.save(user)
            self.collections.create_default(user.id)
            return user

        try:
            user = self.transaction.run(persist)
        except IntegrityError as error:
            diagnostic = getattr(error.orig, "diag", None)
            if getattr(diagnostic, "constraint_name", None) == "uq_users_email_normalized":
                raise duplicate_email() from None
            raise
        return AuthResult(user, self.tokens.issue(user).raw)

    def login(self, email: str, password: str) -> AuthResult:
        user = self.accounts.find_by_email(email.strip().casefold())
        matches = self.passwords.verify(password, user.password_hash if user else self.dummy_hash)
        if not matches or user is None or not user.is_active:
            raise AuthorizationError("Email hoặc mật khẩu chưa đúng.", code=UNAUTHENTICATED)
        return AuthResult(user, self.tokens.issue(user).raw)

    def logout(self, raw_token: str) -> None:
        def action() -> None:
            self.identity.revoke_session(raw_token)

        self.transaction.run(action)
