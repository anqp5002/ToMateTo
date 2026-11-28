"""S9 operations must be reachable through the actual application schema."""

from app.adapters.ai_adapter import AiAdapterFake, AiCompletion
from app.core.config import Config
from app.core.container import AppContainer
from app.core.identity import Principal, SessionVerifier
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


class TestIdentity:
    def verify_session(self, raw_token: str) -> Principal:
        assert raw_token == "fixture-token"  # noqa: S105 - test token
        return Principal(1, "fixture", 1)


class TestWritePolicy:
    def authorize_write(self, principal: Principal, action: str) -> None:
        assert principal.user_id == 1
        assert action in {"askAssistant", "retryAssistant"}


def test_s9_assistant_without_identity_and_policy_fails_closed() -> None:
    def verifier(session: Session) -> SessionVerifier:
        return TestIdentity()

    container = AppContainer(
        Config("postgresql+psycopg://unused/test", "fixture"),
        session_factory=Session,
        session_verifier_factory=verifier,
    )
    query = 'mutation { askAssistant(input:{message:"Món gì?"}) { sessionId } }'
    with TestClient(create_app(container=container)) as client:
        guest = client.post("/graphql", json={"query": query})
        signed_in = client.post(
            "/graphql", json={"query": query}, headers={"Authorization": "Bearer fixture-token"}
        )
    assert guest.json()["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    assert signed_in.json()["errors"][0]["extensions"]["code"] == "FORBIDDEN"


def test_s9_graphql_runs_through_real_app_and_identity_port(
    session_factory: sessionmaker[Session],
) -> None:
    def verifier(session: Session) -> SessionVerifier:
        return TestIdentity()

    container = AppContainer(
        Config("postgresql+psycopg://unused/test", "fixture"),
        session_factory=session_factory,
        session_verifier_factory=verifier,
    )
    app = create_app(
        container=container,
        ai_provider=AiAdapterFake(AiCompletion("gợi ý", post_ids=(200,))),
        write_policy=TestWritePolicy(),
    )
    headers = {"Authorization": "Bearer fixture-token"}
    session_id = None
    try:
        with TestClient(app) as client:
            result = client.post(
                "/graphql",
                json={
                    "query": '{ search(query:"pho", page:{first:2}) '
                    "{ edges { node { type } } pageInfo { hasNextPage } } "
                    "trending { state } }"
                },
            )
            assert result.status_code == 200
            assert result.json()["data"]["search"]["pageInfo"]["hasNextPage"] is True
            assert result.json()["data"]["trending"]["state"] == "WAITING"
            ask = client.post(
                "/graphql",
                headers=headers,
                json={
                    "query": 'mutation { askAssistant(input:{message:"Món gì?"}) '
                    "{ sessionId message { id status content } } }"
                },
            )
            assert ask.status_code == 200
            assert not ask.json().get("errors"), ask.json()
            reply = ask.json()["data"]["askAssistant"]
            session_id = int(reply["sessionId"])
            assert reply["message"]["status"] == "OK"
            history = client.post(
                "/graphql",
                headers=headers,
                json={
                    "query": "query($id:ID!) { assistantHistory(sessionId:$id) "
                    "{ edges { node { role status } } } }",
                    "variables": {"id": str(session_id)},
                },
            )
            assert not history.json().get("errors"), history.json()
            assert len(history.json()["data"]["assistantHistory"]["edges"]) == 2
    finally:
        if session_id is not None:
            from app.repositories.chat_repo import AssistantConversationRepository

            with session_factory.begin() as session:
                AssistantConversationRepository(session).delete_session(session_id, 1)
