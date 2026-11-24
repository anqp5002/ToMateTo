"""T03: revoked session IDs, not refresh tokens."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def is_active(self, now: datetime) -> bool:
        return now < self.expires_at
