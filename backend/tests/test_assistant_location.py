import pytest
from app.adapters.ai_adapter import AiAdapterFake, AiCompletion, PromptContext
from app.core.clock import Clock
from app.core.config import Config
from app.core.container import RequestScope
from app.core.exceptions import IntegrationError, ValidationError
from app.core.identity import Principal, UnavailableSessionVerifier
from app.core.pagination import PageRequest
from app.core.transaction import TransactionManager
from app.repositories.search_repo import SearchRepository
from app.services.assistant_service import AssistantService
from app.services.geo import distance_meters
from sqlalchemy import text
from sqlalchemy.orm import Session


class Policy:
    def authorize_write(self, principal: Principal, action: str) -> None:
        pass


class EchoReference(AiAdapterFake):
    def complete(self, context: PromptContext) -> AiCompletion:
        self.calls.append(context)
        return AiCompletion("Gợi ý", post_ids=(context.posts[0].post_id,))


def test_distance_handles_dateline_and_zero() -> None:
    assert distance_meters(0, 0, 0, 0) == 0
    assert distance_meters(0, 179.99, 0, -179.99) < 5000
    assert distance_meters(0, 0, 1, 0) > 100_000


def test_location_selects_nearby_context_without_persisting_or_forwarding_coordinates(
    db_session: Session,
) -> None:
    # 59 restaurants remain near Hanoi; restaurant 2 alone is in HCMC.
    db_session.execute(
        text("UPDATE restaurants SET latitude=10.7769,longitude=106.7009 WHERE id=2")
    )
    adapter = EchoReference()
    instance = AssistantService(
        RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier()),
        Clock(),
        adapter,
        Policy(),
        nearby_reader=SearchRepository(db_session),
        default_location=(21.0285, 105.8542),
    )
    principal = Principal(1, "jti", 1)
    hanoi = instance.ask("Tìm món", None, principal)
    hcmc = instance.ask("Tìm món", None, principal, (10.7769, 106.7009))
    assert hanoi.message.status == hcmc.message.status == "OK"
    assert adapter.calls[0].posts and adapter.calls[1].posts
    assert all(post.restaurant_id != 2 for post in adapter.calls[0].posts)
    assert all(post.restaurant_id == 2 for post in adapter.calls[1].posts)
    assert "10.7769" not in repr(adapter.calls[1])
    stored = db_session.execute(
        text(
            "SELECT content, context_json FROM chat_messages "
            "JOIN chat_sessions ON chat_sessions.id=chat_messages.session_id "
            "WHERE chat_sessions.id=:id"
        ),
        {"id": hcmc.session_id},
    ).all()
    assert all("10.7769" not in repr(row) for row in stored)


def test_invalid_location_is_rejected_before_saving(db_session: Session) -> None:
    instance = AssistantService(
        RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier()),
        Clock(),
        AiAdapterFake(),
        Policy(),
        nearby_reader=SearchRepository(db_session),
    )
    before = db_session.scalar(text("SELECT count(*) FROM chat_sessions"))
    with pytest.raises(ValidationError):
        instance.ask("Tìm món", None, Principal(1, "jti", 1), (91, 10))
    assert db_session.scalar(text("SELECT count(*) FROM chat_sessions")) == before


def test_retry_uses_default_instead_of_the_previous_request_location(db_session: Session) -> None:
    adapter = AiAdapterFake()
    instance = AssistantService(
        RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier()),
        Clock(),
        adapter,
        Policy(),
        nearby_reader=SearchRepository(db_session),
        default_location=(21.0285, 105.8542),
    )
    principal = Principal(1, "jti", 1)

    # No fixture restaurants are near (0, 0): failing the provider leaves FAILED,
    # which may be retried. The coordinates must not become session context.
    with pytest.raises(IntegrationError):
        instance.ask("Tìm món", None, principal, (0.0, 0.0))
    assert adapter.calls[0].posts == ()
    session = instance.list_sessions(principal, PageRequest.of()).items[0]
    history = instance.history(session.id, principal, PageRequest.of()).items
    reply = next(row for row in history if row.role == "assistant")
    assert reply.status == "FAILED"
    stored_context = db_session.scalar(
        text("SELECT context_json FROM chat_sessions WHERE id=:id"), {"id": session.id}
    )
    assert stored_context == {}

    adapter.response = AiCompletion("Gợi ý", post_ids=(200,))
    assert instance.retry(reply.id, principal).message.status == "OK"
    assert adapter.calls[1].posts
    assert any(post.post_id == 200 for post in adapter.calls[1].posts)


def test_default_location_is_configurable_and_checked() -> None:
    cfg = Config.from_env(
        {
            "DATABASE_URL": "postgresql://localhost/test",
            "JWT_SECRET": "x",
            "ASSISTANT_DEFAULT_LATITUDE": "10.7769",
            "ASSISTANT_DEFAULT_LONGITUDE": "106.7009",
        }
    )
    assert (cfg.assistant_default_latitude, cfg.assistant_default_longitude) == (10.7769, 106.7009)
    with pytest.raises(ValueError):
        Config("postgresql://localhost/test", "x", assistant_default_latitude=91)
