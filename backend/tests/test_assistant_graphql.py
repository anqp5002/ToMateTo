from collections.abc import Iterator

import pytest
from app.adapters.ai_adapter import AiAdapterFake, AiCompletion
from app.core.clock import Clock
from app.core.config import Config
from app.core.container import AppContainer, RequestScope
from app.core.identity import Principal, SessionVerifier
from app.graphql.assistant import AssistantMutation, AssistantQuery
from app.graphql.schema import SafeSchema
from app.main import create_app
from app.repositories.chat_repo import AssistantConversationRepository
from app.repositories.search_repo import SearchRepository
from app.services.assistant_service import AssistantService
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker


class Verifier:
    def verify_session(self, raw_token: str) -> Principal:
        return Principal(1, "test", 1)


class AllowWrites:
    def authorize_write(self, principal: Principal, action: str) -> None:
        assert principal.user_id == 1


@pytest.fixture
def clean_conversations(session_factory: sessionmaker[Session]) -> Iterator[None]:
    with session_factory() as session:
        before = set(session.scalars(text("SELECT id FROM chat_sessions WHERE user_id=1")))
    yield
    with session_factory.begin() as session:
        after = set(session.scalars(text("SELECT id FROM chat_sessions WHERE user_id=1")))
        for session_id in after - before:
            AssistantConversationRepository(session).delete_session(session_id, 1)


def test_assistant_graphql_round_trip(
    session_factory: sessionmaker[Session], clean_conversations: None
) -> None:
    def identity(session: Session) -> SessionVerifier:
        return Verifier()

    container = AppContainer(
        Config("postgresql+psycopg://unused/test", "fixture"),
        session_factory=session_factory,
        session_verifier_factory=identity,
    )
    app = create_app(
        container=container, schema=SafeSchema(query=AssistantQuery, mutation=AssistantMutation)
    )
    adapter = AiAdapterFake(AiCompletion("ok", post_ids=(200,)))

    def factory(scope: RequestScope, clock: Clock) -> AssistantService:
        return AssistantService(
            scope, clock, adapter, AllowWrites(), nearby_reader=SearchRepository(scope.session)
        )

    app.state.assistant_service_factory = factory
    with TestClient(app) as client:
        response = client.post(
            "/graphql",
            json={
                "query": 'mutation { askAssistant(input: {message: "Ăn gì?", '
                "location: {latitude: 21.0285, longitude: 105.8542}}) "
                "{ sessionId message { id status content } } }"
            },
            headers={"Authorization": "Bearer fixture"},
        )
        assert response.status_code == 200
        assert "errors" not in response.json()
        reply = response.json()["data"]["askAssistant"]
        assert reply["message"]["status"] == "OK"
        response = client.post(
            "/graphql",
            json={
                "query": "{ assistantSessions { edges { node { id lastMessageAt } } "
                "pageInfo { hasNextPage } } }"
            },
            headers={"Authorization": "Bearer fixture"},
        )
        assert (
            response.json()["data"]["assistantSessions"]["edges"][0]["node"]["id"]
            == reply["sessionId"]
        )
