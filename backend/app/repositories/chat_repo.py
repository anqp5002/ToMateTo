"""Owner-scoped conversation persistence and retry compare-and-set operations.

The caller owns the transaction and commits a claim before contacting the AI provider.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import CursorCodec, LatestCursor, PageRequest
from app.models.chat import ChatMessage, ChatSession
from app.repositories.page import RepositoryPage


@dataclass(frozen=True)
class ReplyResult:
    status: str
    content: str
    post_draft: dict[str, object] | None = None


@dataclass(frozen=True)
class ClaimResult:
    state: Literal["CLAIMED", "BUSY", "COMPLETED"]
    reply_id: int
    processing_version: int
    current_reply: ChatMessage

    @classmethod
    def from_reply(
        cls, state: Literal["CLAIMED", "BUSY", "COMPLETED"], reply: ChatMessage
    ) -> "ClaimResult":
        return cls(state, reply.id, reply.processing_version, reply)


@dataclass(frozen=True)
class SessionSummary:
    id: int
    created_at: datetime
    last_message_at: datetime | None


def _require_aware(now: datetime) -> None:
    if now.utcoffset() is None:
        raise ValidationError(message="Thời điểm xử lý trợ lý phải có múi giờ.")


class AssistantConversationRepository:
    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        self._session = session
        self._codec = CursorCodec()
        self._clock = clock or Clock()

    def create_session(self, user_id: int) -> ChatSession:
        conversation = ChatSession(user_id=user_id, context_json={})
        self._session.add(conversation)
        self._session.flush()
        return conversation

    def find_session(self, session_id: int, owner_id: int) -> ChatSession | None:
        return self._session.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == owner_id,
            )
        )

    def list_sessions(self, owner_id: int, page: PageRequest) -> RepositoryPage[SessionSummary]:
        scope = f"assistant-sessions:{owner_id}"
        query = select(ChatSession.id, ChatSession.created_at).where(
            ChatSession.user_id == owner_id
        )
        if page.after is not None:
            key = self._codec.decode(page.after, "LATEST", scope=scope)
            if not isinstance(key, LatestCursor):
                raise ValidationError()
            query = query.where(
                (ChatSession.created_at < key.created_at)
                | ((ChatSession.created_at == key.created_at) & (ChatSession.id < key.item_id))
            )
        sessions = (
            query.order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .limit(page.first + 1)
            .cte("session_page")
        )
        last_messages = (
            select(
                ChatMessage.session_id, func.max(ChatMessage.created_at).label("last_message_at")
            )
            .join(sessions, ChatMessage.session_id == sessions.c.id)
            .group_by(ChatMessage.session_id)
            .subquery()
        )
        rows = self._session.execute(
            select(sessions.c.id, sessions.c.created_at, last_messages.c.last_message_at)
            .outerjoin(last_messages, last_messages.c.session_id == sessions.c.id)
            .order_by(sessions.c.created_at.desc(), sessions.c.id.desc())
        )
        return RepositoryPage.from_rows(
            [SessionSummary(*row) for row in rows],
            page,
            lambda item: self._codec.encode_latest(item.created_at, item.id, scope=scope),
        )

    def save_message(self, message: ChatMessage, owner_id: int) -> ChatMessage:
        """Save a user question. Assistant replies use claim_reply and complete_reply."""
        if message.role != "user":
            raise ValidationError(message="Phản hồi trợ lý phải đi qua luồng xử lý phiên bản.")
        if (
            self._session.scalar(
                select(ChatSession.id).where(
                    ChatSession.id == message.session_id, ChatSession.user_id == owner_id
                )
            )
            is None
        ):
            raise NotFoundError()
        self._session.add(message)
        self._session.flush()
        return message

    def find_message(self, message_id: int, owner_id: int) -> ChatMessage | None:
        return self._session.scalar(
            select(ChatMessage)
            .join(ChatSession)
            .where(
                ChatMessage.id == message_id,
                ChatSession.user_id == owner_id,
            )
        )

    def list_messages(
        self, session_id: int, owner_id: int, page: PageRequest
    ) -> RepositoryPage[ChatMessage]:
        scope = f"assistant-history:{owner_id}:{session_id}"
        query = (
            select(ChatMessage)
            .join(ChatSession)
            .where(
                ChatMessage.session_id == session_id,
                ChatSession.user_id == owner_id,
            )
        )
        if page.after is not None:
            key = self._codec.decode(page.after, "LATEST", scope=scope)
            if not isinstance(key, LatestCursor):
                raise ValidationError()
            query = query.where(
                (ChatMessage.created_at < key.created_at)
                | ((ChatMessage.created_at == key.created_at) & (ChatMessage.id < key.item_id))
            )
        rows = list(
            self._session.scalars(
                query.order_by(
                    ChatMessage.created_at.desc(),
                    ChatMessage.id.desc(),
                ).limit(page.first + 1)
            )
        )
        return RepositoryPage.from_rows(
            rows,
            page,
            lambda item: self._codec.encode_latest(item.created_at, item.id, scope=scope),
        )

    def claim_reply(
        self, user_message_id: int, owner_id: int, now: datetime, lease_seconds: int
    ) -> ClaimResult:
        """Refresh time after locking so lock waits cannot revive an expired lease."""
        _require_aware(now)
        if lease_seconds <= 0 or lease_seconds > 30:
            raise ValidationError(message="Thời hạn xử lý trợ lý không hợp lệ.")
        question = self._session.scalar(
            select(ChatMessage)
            .join(ChatSession)
            .where(
                ChatMessage.id == user_message_id,
                ChatMessage.role == "user",
                ChatSession.user_id == owner_id,
            )
            .with_for_update(of=ChatMessage)
        )
        if question is None:
            raise ValidationError(message="Không xác định được câu hỏi của phiên.")
        reply = self._session.scalar(
            select(ChatMessage)
            .where(
                ChatMessage.reply_to_id == user_message_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        now = max(now, self._clock.now())
        if reply is None:
            reply = ChatMessage(
                session_id=question.session_id,
                reply_to_id=question.id,
                role="assistant",
                content="",
                status="PENDING",
                processing_version=1,
                processing_expires_at=now + timedelta(seconds=lease_seconds),
            )
            self._session.add(reply)
            self._session.flush()
            return ClaimResult.from_reply("CLAIMED", reply)
        if reply.status in {"OK", "FALLBACK"}:
            return ClaimResult.from_reply("COMPLETED", reply)
        if (
            reply.status == "PENDING"
            and reply.processing_expires_at is not None
            and reply.processing_expires_at > now
        ):
            return ClaimResult.from_reply("BUSY", reply)
        reply.processing_version += 1
        reply.processing_expires_at = now + timedelta(seconds=lease_seconds)
        reply.status = "PENDING"
        reply.content = ""
        reply.post_draft = None
        reply.updated_at = now
        self._session.flush()
        return ClaimResult.from_reply("CLAIMED", reply)

    def complete_reply(
        self,
        reply_id: int,
        owner_id: int,
        processing_version: int,
        result: ReplyResult,
        now: datetime,
    ) -> bool:
        _require_aware(now)
        if result.status not in {"OK", "FAILED", "FALLBACK"}:
            raise ValidationError(message="Trạng thái phản hồi không hợp lệ.")
        locked = self._session.scalar(
            select(ChatMessage.id)
            .join(ChatSession)
            .where(
                ChatMessage.id == reply_id,
                ChatSession.user_id == owner_id,
            )
            .with_for_update(of=ChatMessage)
        )
        if locked is None:
            return False
        now = max(now, self._clock.now())
        owner = exists(
            select(ChatSession.id).where(
                ChatSession.id == ChatMessage.session_id,
                ChatSession.user_id == owner_id,
            )
        )
        changed = self._session.scalar(
            update(ChatMessage)
            .where(
                ChatMessage.id == reply_id,
                ChatMessage.role == "assistant",
                owner,
                ChatMessage.processing_version == processing_version,
                ChatMessage.status == "PENDING",
                ChatMessage.processing_expires_at > now,
            )
            .values(
                status=result.status,
                content=result.content,
                post_draft=result.post_draft,
                processing_expires_at=None,
                updated_at=now,
            )
            .returning(ChatMessage.id)
        )
        return changed is not None

    def delete_session(self, session_id: int, owner_id: int) -> bool:
        """Internal retention primitive; no public delete-session API is added."""
        conversation = self._session.scalar(
            select(ChatSession)
            .where(
                ChatSession.id == session_id,
                ChatSession.user_id == owner_id,
            )
            .with_for_update()
        )
        if conversation is None:
            return False
        self._session.execute(
            delete(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "assistant",
            )
        )
        self._session.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        self._session.delete(conversation)
        self._session.flush()
        return True
