from datetime import UTC, datetime
from time import monotonic, sleep
from unittest.mock import MagicMock

import pytest
from app.adapters.ai_adapter import AiAdapter, AiAdapterFake, AiCompletion, PromptContext
from app.core.clock import Clock
from app.core.container import RequestScope
from app.core.exceptions import AuthorizationError, IntegrationError, NotFoundError
from app.core.identity import Principal, UnavailableSessionVerifier
from app.core.pagination import PageRequest
from app.core.transaction import TransactionManager
from app.repositories.chat_repo import (
    AssistantConversationRepository,
    HistoryContextRow,
    PublicContextRow,
)
from app.repositories.search_repo import NearbyCandidate, SearchRepository
from app.services.assistant_service import AssistantService, UnavailableWritePolicy
from sqlalchemy import text
from sqlalchemy.orm import Session


class Policy:
    def authorize_write(self, principal: Principal, action: str) -> None:
        assert principal.user_id > 0
        assert action in {"askAssistant", "retryAssistant"}


def test_prompt_assembly_uses_repository_and_sanitizes_without_database() -> None:
    repository = MagicMock(spec=AssistantConversationRepository)
    repository.list_public_context.return_value = [
        PublicContextRow(10, 20, "Phở", "Email: an@example.com", None, None)
    ]
    repository.list_history_before.return_value = [
        HistoryContextRow("assistant", "near 21.03, 105.85"),
        HistoryContextRow("user", "câu hỏi trước"),
    ]
    instance = object.__new__(AssistantService)
    instance.repo = repository

    prompt = instance._prompt_context(4, "Tìm món", 7, 9)

    repository.list_public_context.assert_called_once_with(7, 10)
    repository.list_history_before.assert_called_once_with(9, 4, 7, 10)
    assert prompt.posts[0].caption == "Email: [đã ẩn]"
    assert [item.role for item in prompt.history] == ["user", "assistant"]
    assert prompt.history[-1].content == "near [đã ẩn vị trí]"


def test_location_context_uses_injected_nearby_reader_without_database() -> None:
    class NearbyFake:
        def __init__(self) -> None:
            self.calls: list[tuple[float, float]] = []

        def find_nearby(
            self, latitude: float, longitude: float, radius_meters: int = 5000
        ) -> list[NearbyCandidate]:
            self.calls.append((latitude, longitude))
            return [
                NearbyCandidate(3, "Near", latitude, longitude),
                NearbyCandidate(4, "Far", 0, 0),
            ]

    session = MagicMock(spec=Session)
    scope = RequestScope(session, TransactionManager(session), UnavailableSessionVerifier())
    reader = NearbyFake()
    instance = AssistantService(scope, Clock(), AiAdapterFake(), Policy(), nearby_reader=reader)
    repository = MagicMock(spec=AssistantConversationRepository)
    repository.list_public_context.return_value = [PublicContextRow(10, 20, "Phở", "", 3, "Near")]
    instance.repo = repository

    context = instance._public_context("Gợi ý", 7, (21.0285, 105.8542))

    assert reader.calls == [(21.0285, 105.8542)]
    repository.list_public_context.assert_called_once_with(7, 10, {3})
    assert context.posts[0].restaurant_id == 3
    session.execute.assert_not_called()


def service(session: Session, adapter: AiAdapterFake) -> AssistantService:
    return AssistantService(
        RequestScope(session, TransactionManager(session), UnavailableSessionVerifier()),
        Clock(),
        adapter,
        Policy(),
        nearby_reader=SearchRepository(session),
    )


def test_ask_commits_pending_before_provider_and_returns_existing_history(
    db_session: Session,
) -> None:
    principal = Principal(1, "jti", 1)

    class CommittedAdapter(AiAdapterFake):
        def complete(self, context: PromptContext) -> AiCompletion:
            assert not db_session.in_transaction()
            return super().complete(context)

    adapter = CommittedAdapter(AiCompletion("Món phở phù hợp.", post_ids=(200,)))
    instance = service(db_session, adapter)
    result = instance.ask("Ăn gì?", None, principal)
    assert result.message.status == "OK"
    history = instance.history(result.session_id, principal, PageRequest.of())
    assert {m.role for m in history.items} == {"user", "assistant"}
    assert len(adapter.calls) == 1


def test_provider_failure_saves_fallback_and_does_not_duplicate_question(
    db_session: Session,
) -> None:
    principal = Principal(1, "jti", 1)
    adapter = AiAdapterFake()
    instance = service(db_session, adapter)
    with pytest.raises(IntegrationError):
        instance.ask("Ăn gì?", None, principal)
    session = instance.list_sessions(principal, PageRequest.of()).items[0]
    history = instance.history(session.id, principal, PageRequest.of()).items
    reply = next(m for m in history if m.role == "assistant")
    assert reply.status == "FALLBACK"
    assert instance.retry(reply.id, principal).message.id == reply.id
    assert len(adapter.calls) == 1
    assert len(instance.history(session.id, principal, PageRequest.of()).items) == 2


def test_slow_provider_timeout_saves_fallback_in_service(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    class SlowClient:
        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "SlowClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def post(self, *args: object, **kwargs: object) -> None:
            sleep(2)
            raise RuntimeError("provider failed")

    monkeypatch.setattr("app.adapters.ai_adapter.httpx.Client", SlowClient)
    scope = RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier())
    adapter = AiAdapter("https://example.invalid", "fixture", timeout_seconds=0.05)
    instance = AssistantService(
        scope, Clock(), adapter, Policy(), nearby_reader=SearchRepository(db_session)
    )
    principal = Principal(1, "jti", 1)
    started = monotonic()
    with pytest.raises(IntegrationError):
        instance.ask("Ăn gì?", None, principal)
    assert monotonic() - started < 1.5
    sid = instance.list_sessions(principal, PageRequest.of()).items[0].id
    reply = next(
        m for m in instance.history(sid, principal, PageRequest.of()).items if m.role == "assistant"
    )
    assert reply.status == "FALLBACK"


def test_reference_validation_keeps_valid_and_discards_unseen_ids(db_session: Session) -> None:
    adapter = AiAdapterFake(
        AiCompletion(
            "Một món không có thật.",
            post_ids=(200, 999999),
            dish_ids=(999998,),
            restaurant_ids=(999997,),
        )
    )
    instance = service(db_session, adapter)
    result = instance.ask("Ăn gì?", None, Principal(1, "jti", 1))
    assert result.message.status == "OK"
    assert "Phở" in result.message.content
    assert "không có thật" not in result.message.content


def test_reference_validation_falls_back_when_no_reference_is_valid(db_session: Session) -> None:
    adapter = AiAdapterFake(AiCompletion("Một món không có thật.", post_ids=(999999,)))
    instance = service(db_session, adapter)
    principal = Principal(1, "jti", 1)
    with pytest.raises(IntegrationError):
        instance.ask("Ăn gì?", None, principal)
    session = instance.list_sessions(principal, PageRequest.of()).items[0]
    history = instance.history(session.id, principal, PageRequest.of()).items
    reply = next(m for m in history if m.role == "assistant")
    assert reply.status == "FALLBACK"
    assert "không có thật" not in reply.content


def test_empty_context_failure_is_failed_and_retry_updates_same_reply(db_session: Session) -> None:
    db_session.execute(text("UPDATE posts SET is_hidden=true"))
    adapter = AiAdapterFake()
    instance = service(db_session, adapter)
    principal = Principal(1, "jti", 1)
    with pytest.raises(IntegrationError):
        instance.ask("Ăn gì?", None, principal)
    session = instance.list_sessions(principal, PageRequest.of()).items[0]
    rows = instance.history(session.id, principal, PageRequest.of()).items
    reply = next(m for m in rows if m.role == "assistant")
    assert reply.status == "FAILED"
    db_session.execute(text("UPDATE posts SET is_hidden=false WHERE id=1"))
    db_session.commit()
    adapter.response = AiCompletion("Xin thử thêm món khác.", post_ids=(1,))
    assert instance.retry(reply.id, principal).message.status == "OK"
    assert len(instance.history(session.id, principal, PageRequest.of()).items) == 2


def test_owner_and_policy_fail_closed(db_session: Session) -> None:
    adapter = AiAdapterFake(AiCompletion("ok", post_ids=(200,)))
    scope = RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier())
    instance = AssistantService(
        scope,
        Clock(),
        adapter,
        UnavailableWritePolicy(),
        nearby_reader=SearchRepository(db_session),
    )
    with pytest.raises(AuthorizationError):
        instance.ask("Ăn gì?", None, Principal(1, "jti", 1))
    instance = service(db_session, adapter)
    result = instance.ask("Ăn gì?", None, Principal(1, "jti", 1))
    with pytest.raises(NotFoundError):
        instance.history(result.session_id, Principal(2, "jti", 1), PageRequest.of())
    with pytest.raises(NotFoundError):
        instance.retry(result.message.id, Principal(2, "jti", 1))
    assert datetime.now(UTC).tzinfo


def test_prompt_includes_only_ten_sanitized_prior_messages_for_own_session(
    db_session: Session,
) -> None:
    instance = service(db_session, AiAdapterFake(AiCompletion("ok", post_ids=(200,))))
    session = instance.repo.create_session(1)
    other_session = instance.repo.create_session(1)
    outsider_session = instance.repo.create_session(2)
    db_session.execute(
        text("""
            INSERT INTO chat_messages(session_id,role,status,content,created_at)
            SELECT :sid,'user','OK',
                   CASE WHEN i=12 THEN 'mail an@example.com token Bearer secret'
                        ELSE 'câu cũ ' || i END,
                   '2025-01-01 UTC'::timestamptz + (i * interval '1 second')
            FROM generate_series(1,12) AS i
        """),
        {"sid": session.id},
    )
    for session_id in (other_session.id, outsider_session.id):
        db_session.execute(
            text("""
                INSERT INTO chat_messages(session_id,role,status,content,created_at)
                VALUES(:sid,'user','OK','KHONG DUOC LO','2025-01-02 UTC')
            """),
            {"sid": session_id},
        )
    adapter = instance.adapter
    assert isinstance(adapter, AiAdapterFake)
    instance.ask("Câu hỏi hiện tại?", session.id, Principal(1, "jti", 1))
    prompt = adapter.calls[-1]
    assert len(prompt.history) == 10
    assert prompt.history[0].content == "câu cũ 3"
    assert prompt.history[-1].content == "mail [đã ẩn] token [đã ẩn]"
    history = " ".join(message.content for message in prompt.history)
    assert "Câu hỏi hiện tại?" not in history
    assert "KHONG DUOC LO" not in history
    assert "an@example.com" not in history
    assert "secret" not in history


def test_coordinates_are_removed_before_storage_and_provider_context(db_session: Session) -> None:
    adapter = AiAdapterFake(AiCompletion("ok", post_ids=(200,)))
    instance = service(db_session, adapter)
    conversation = instance.repo.create_session(1)
    db_session.execute(
        text("UPDATE posts SET caption=:caption WHERE id=200"),
        {"caption": "x" * 192 + " 21.03, 105.85"},
    )
    db_session.execute(
        text("""
            INSERT INTO chat_messages(session_id, role, status, content, created_at)
            VALUES(:sid, 'user', 'OK', :content, '2025-01-01 UTC')
        """),
        {"sid": conversation.id, "content": "x" * 1990 + " 21.03, 105.85"},
    )
    instance.ask("Tìm món ở 21.03, 105.85", conversation.id, Principal(1, "jti", 1))
    prompt = adapter.calls[-1]
    assert "21.03" not in prompt.question and "105.85" not in prompt.question
    assert "[đã ẩn vị trí]" in prompt.question
    assert all("21.03" not in post.caption for post in prompt.posts)
    assert all("21.03" not in message.content for message in prompt.history)
    rows = instance.history(conversation.id, Principal(1, "jti", 1), PageRequest.of()).items
    current_question = next(row.content for row in rows if row.content.startswith("Tìm món"))
    assert "21.03" not in current_question and "105.85" not in current_question
