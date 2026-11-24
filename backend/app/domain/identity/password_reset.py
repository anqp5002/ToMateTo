"""T02: one row contains the OTP and the single-use reset grant."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    otp_hash: Mapped[str] = mapped_column(Text)
    failed_attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reset_token_hash: Mapped[str | None] = mapped_column(Text)
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def register_failed_attempt(self, now: datetime) -> None:
        self.failed_attempts = min(self.failed_attempts + 1, 5)
        if self.failed_attempts == 5:
            self.invalidated_at = now

    def is_otp_valid(self, now: datetime) -> bool:
        return (
            self.invalidated_at is None
            and self.verified_at is None
            and self.consumed_at is None
            and self.failed_attempts < 5
            and now < self.otp_expires_at
        )

    def consume(self, now: datetime) -> None:
        if (
            self.verified_at is None
            or self.invalidated_at is not None
            or self.consumed_at is not None
            or self.reset_expires_at is None
            or now >= self.reset_expires_at
        ):
            raise ValueError("Reset grant is not usable.")
        self.consumed_at = now
