"""T18/T19 constraints on PostgreSQL, including retry-state invariants."""

from datetime import UTC, datetime, timedelta

import pytest
from app.models.chat import ChatMessage, ChatSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_unique_reply_and_status_checks(db_session: Session) -> None:
    conversation = ChatSession(user_id=1)
    db_session.add(conversation)
    db_session.flush()
    question = ChatMessage(session_id=conversation.id, role="user", content="Món gì?", status="OK")
    db_session.add(question)
    db_session.flush()
    reply = ChatMessage(
        session_id=conversation.id,
        reply_to_id=question.id,
        role="assistant",
        content="",
        status="PENDING",
        processing_version=1,
        processing_expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )
    db_session.add(reply)
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            ChatMessage(
                session_id=conversation.id,
                reply_to_id=question.id,
                role="assistant",
                content="",
                status="FAILED",
                processing_version=1,
            )
        )
        db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            ChatMessage(session_id=conversation.id, role="user", content="x", status="DONE")
        )
        db_session.flush()


@pytest.mark.parametrize(
    "role,status,version,has_expiry",
    [
        ("user", "FAILED", 0, False),
        ("assistant", "PENDING", 1, False),
        ("assistant", "OK", 1, True),
        ("assistant", "OK", 0, False),
    ],
)
def test_processing_shape_is_enforced(
    db_session: Session, role: str, status: str, version: int, has_expiry: bool
) -> None:
    conversation = ChatSession(user_id=1)
    db_session.add(conversation)
    db_session.flush()
    question = ChatMessage(session_id=conversation.id, role="user", content="q", status="OK")
    db_session.add(question)
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            ChatMessage(
                session_id=conversation.id,
                reply_to_id=question.id if role == "assistant" else None,
                role=role,
                content="x",
                status=status,
                processing_version=version,
                processing_expires_at=datetime.now(UTC) if has_expiry else None,
            )
        )
        db_session.flush()


@pytest.mark.parametrize(
    ("has_reply", "draft", "constraint"),
    [
        (True, None, "ck_chat_messages_reply"),
        (False, {"dishName": "Phở"}, "ck_chat_messages_draft"),
    ],
)
def test_user_question_cannot_have_reply_link_or_draft(
    has_reply: bool, draft: dict[str, object] | None, constraint: str, db_session: Session
) -> None:
    conversation = ChatSession(user_id=1)
    db_session.add(conversation)
    db_session.flush()
    question = ChatMessage(session_id=conversation.id, role="user", content="q", status="OK")
    db_session.add(question)
    db_session.flush()
    with pytest.raises(IntegrityError, match=constraint), db_session.begin_nested():
        db_session.add(
            ChatMessage(
                session_id=conversation.id,
                reply_to_id=question.id if has_reply else None,
                role="user",
                content="x",
                status="OK",
                post_draft=draft,
            )
        )
        db_session.flush()
