"""Owner isolation and compare-and-set protection for conversation storage."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from app.core.clock import Clock
from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import PageRequest
from app.models.chat import ChatMessage
from app.repositories.chat_repo import AssistantConversationRepository, ReplyResult
from sqlalchemy.orm import Session, sessionmaker


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 11, 18, tzinfo=UTC)


def test_save_message_rejects_unguarded_assistant_reply() -> None:
    with Session() as session:
        repo = AssistantConversationRepository(session)
        reply = ChatMessage(session_id=1, reply_to_id=1, role="assistant", content="x", status="OK")
        with pytest.raises(ValidationError):
            repo.save_message(reply, 1)


def test_owner_lookup_and_versioned_completion(db_session: Session) -> None:
    repo = AssistantConversationRepository(db_session, FixedClock())
    conversation = repo.create_session(1)
    assert repo.find_session(conversation.id, 2) is None  # TC-BE-1804 owner isolation.
    question = repo.save_message(
        ChatMessage(session_id=conversation.id, role="user", content="Phở?", status="OK"), 1
    )
    now = datetime(2026, 11, 18, tzinfo=UTC)
    first = repo.claim_reply(question.id, 1, now, 30)
    assert first.state == "CLAIMED"
    assert repo.claim_reply(question.id, 1, now + timedelta(seconds=1), 30).state == "BUSY"
    assert repo.find_message(first.reply_id, 2) is None
    next_claim = repo.claim_reply(question.id, 1, now + timedelta(seconds=31), 30)
    assert next_claim.state == "CLAIMED" and next_claim.processing_version == 2
    assert next_claim.reply_id == first.reply_id and first.processing_version == 1
    assert not repo.complete_reply(
        first.reply_id, 1, 1, ReplyResult("OK", "Old"), now + timedelta(seconds=32)
    )
    assert repo.complete_reply(
        first.reply_id, 1, 2, ReplyResult("OK", "New"), now + timedelta(seconds=32)
    )
    assert repo.list_messages(conversation.id, 1, PageRequest.of()).items[0].content == "New"
    final = repo.claim_reply(question.id, 1, now + timedelta(seconds=60), 30)
    assert final.state == "COMPLETED" and final.current_reply.content == "New"


def test_delete_session_removes_only_its_messages(db_session: Session) -> None:
    repo = AssistantConversationRepository(db_session)
    own, other = repo.create_session(1), repo.create_session(2)
    own_question = repo.save_message(
        ChatMessage(session_id=own.id, role="user", content="q", status="OK"), 1
    )
    other_question = repo.save_message(
        ChatMessage(session_id=other.id, role="user", content="q", status="OK"), 2
    )
    now = datetime(2026, 11, 18, tzinfo=UTC)
    repo.claim_reply(own_question.id, 1, now, 30)
    assert not repo.delete_session(own.id, 2)
    assert repo.delete_session(own.id, 1)
    assert repo.find_session(own.id, 1) is None
    assert repo.find_message(other_question.id, 2) is not None


def test_history_keyset_cannot_be_reused_for_another_owner(db_session: Session) -> None:
    repo = AssistantConversationRepository(db_session)
    conversation = repo.create_session(1)
    for number in range(3):
        repo.save_message(
            ChatMessage(session_id=conversation.id, role="user", content=str(number), status="OK"),
            1,
        )
    first = repo.list_messages(conversation.id, 1, PageRequest.of(2))
    second = repo.list_messages(conversation.id, 1, PageRequest.of(2, first.next_cursor))
    assert [item.content for item in first.items] == ["2", "1"]
    assert [item.content for item in second.items] == ["0"]
    assert not repo.list_messages(conversation.id, 2, PageRequest.of()).items
    with pytest.raises(ValidationError):
        repo.list_messages(conversation.id, 2, PageRequest.of(2, first.next_cursor))


def test_two_connections_claim_one_logical_reply(session_factory: sessionmaker[Session]) -> None:
    with session_factory.begin() as session:
        repo = AssistantConversationRepository(session)
        conversation = repo.create_session(1)
        question = repo.save_message(
            ChatMessage(session_id=conversation.id, role="user", content="race", status="OK"), 1
        )
        question_id, session_id = question.id, conversation.id
    barrier = Barrier(2)

    def claim() -> bool:
        with session_factory.begin() as session:
            barrier.wait(timeout=5)
            result = AssistantConversationRepository(session).claim_reply(
                question_id,
                1,
                Clock().now(),
                30,
            )
            return result.state == "CLAIMED"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(claim)
            second = workers.submit(claim)
            assert sorted([first.result(timeout=10), second.result(timeout=10)]) == [False, True]
        with session_factory() as session:
            repo = AssistantConversationRepository(session)
            rows = repo.list_messages(session_id, 1, PageRequest.of()).items
            assert len(rows) == 2
            reply = next(row for row in rows if row.role == "assistant")
            assert reply.processing_version == 1
    finally:
        with session_factory.begin() as session:
            AssistantConversationRepository(session).delete_session(session_id, 1)


def test_session_list_projects_last_message_and_filters_owner_before_paging(
    db_session: Session,
) -> None:
    repo = AssistantConversationRepository(db_session)
    with_message, empty = repo.create_session(1), repo.create_session(1)
    repo.create_session(2)
    message = ChatMessage(session_id=with_message.id, role="user", content="q", status="OK")
    with pytest.raises(NotFoundError):
        repo.save_message(message, 2)
    repo.save_message(message, 1)
    page = repo.list_sessions(1, PageRequest.of(1))
    assert [(x.id, x.last_message_at) for x in page.items] == [(empty.id, None)]
    next_page = repo.list_sessions(1, PageRequest.of(1, page.next_cursor))
    assert [(x.id, x.last_message_at) for x in next_page.items] == [
        (with_message.id, message.created_at)
    ]
    assert not next_page.has_next


@pytest.mark.parametrize(
    ("status", "next_state"), [("FAILED", "CLAIMED"), ("FALLBACK", "COMPLETED")]
)
def test_claim_retries_failed_but_reuses_fallback(
    status: str, next_state: str, db_session: Session
) -> None:
    repo = AssistantConversationRepository(db_session, FixedClock())
    conversation = repo.create_session(1)
    question = repo.save_message(
        ChatMessage(session_id=conversation.id, role="user", content="q", status="OK"), 1
    )
    now = FixedClock().now()
    first = repo.claim_reply(question.id, 1, now, 30)
    assert repo.complete_reply(
        first.reply_id, 1, first.processing_version, ReplyResult(status, "x"), now
    )
    again = repo.claim_reply(question.id, 1, now, 30)
    assert again.state == next_state
    assert again.reply_id == first.reply_id
    assert again.processing_version == (2 if status == "FAILED" else 1)
