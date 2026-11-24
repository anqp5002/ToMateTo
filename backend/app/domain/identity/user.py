"""T01 users: physical columns follow DOC 6.4-B."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ARRAY, BigInteger, Boolean, DateTime, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text)
    email_normalized: Mapped[str] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(Text)
    username_normalized: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    social_links: Mapped[dict[str, str]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    public_profile_fields: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default=text("'{}'::text[]")
    )
    avatar_media_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    cover_media_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    token_version: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def change_password(self, password_hash: str) -> None:
        """Caller locks this account before changing password and consuming a grant."""
        self.password_hash = password_hash
        self.token_version += 1
