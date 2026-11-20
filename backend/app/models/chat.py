"""T18/T19 persistence models matching DOC 6.4-B."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, user_reference


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_chat_sessions"),
        Index("ix_chat_sessions_owner_cursor", "user_id", text("created_at DESC"), text("id DESC")),
        CheckConstraint("jsonb_typeof(context_json) = 'object'", name="ck_chat_sessions_context"),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= created_at", name="ck_chat_sessions_end_time"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            user_reference.c.id,
            name="fk_chat_sessions_user_id",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    context_json: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_chat_messages"),
        Index("ix_chat_messages_history", "session_id", "created_at", "id"),
        Index("ix_chat_messages_session_reply", "session_id", "reply_to_id"),
        UniqueConstraint("reply_to_id", name="uq_chat_messages_reply_to_id"),
        CheckConstraint("role IN ('user','assistant')", name="ck_chat_messages_role"),
        CheckConstraint(
            "status IN ('PENDING','OK','FAILED','FALLBACK')", name="ck_chat_messages_status"
        ),
        CheckConstraint(
            "(role = 'user' AND reply_to_id IS NULL) OR "
            "(role = 'assistant' AND reply_to_id IS NOT NULL)",
            name="ck_chat_messages_reply",
        ),
        CheckConstraint(
            "post_draft IS NULL OR (jsonb_typeof(post_draft) = 'object' "
            "AND role = 'assistant' AND status IN ('OK','FALLBACK'))",
            name="ck_chat_messages_draft",
        ),
        CheckConstraint(
            "(role = 'user' AND status = 'OK' AND processing_version = 0 "
            "AND processing_expires_at IS NULL) OR (role = 'assistant' "
            "AND processing_version >= 1 AND ((status = 'PENDING' "
            "AND processing_expires_at IS NOT NULL) OR (status <> 'PENDING' "
            "AND processing_expires_at IS NULL)))",
            name="ck_chat_messages_processing",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "chat_sessions.id",
            name="fk_chat_messages_session_id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    reply_to_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "chat_messages.id",
            name="fk_chat_messages_reply_to_id",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
    )
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    post_draft: Mapped[dict[str, object] | None] = mapped_column(JSONB(none_as_null=True))
    processing_version: Mapped[int] = mapped_column(BigInteger, default=0, server_default=text("0"))
    processing_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
