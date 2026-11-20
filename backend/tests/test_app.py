import threading
from uuid import UUID

import pytest
import strawberry
from app.core.config import Config
from app.core.container import AppContainer
from app.core.exceptions import ValidationError
from app.core.identity import Principal, SessionVerifier
from app.graphql.context import RequestContext
from app.graphql.schema import SafeSchema
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from strawberry.types import Info


class RecordingVerifier:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def verify_session(self, token: str) -> Principal:
        self.calls.append(token)
        return Principal(1, "fixture-jti", 1)


def test_typename_passes_context_and_returns_request_id() -> None:
    verifier = RecordingVerifier()

    def factory(session: Session) -> SessionVerifier:
        return verifier

    container = AppContainer(
        Config("unused", "fixture"), session_factory=Session, session_verifier_factory=factory
    )
    with TestClient(create_app(container=container)) as client:
        result = client.post(
            "/graphql",
            json={"query": "{ __typename }"},
            headers={"Authorization": "Bearer fixture-token"},
        )
    assert result.status_code == 200
    assert result.json() == {"data": {"__typename": "Query"}}
    assert result.headers["X-Request-Id"]
    assert verifier.calls == ["fixture-token"]


@strawberry.type
class ProbeQuery:
    @strawberry.field
    def service_error(self) -> str:
        raise ValidationError()

    @strawberry.field
    def unexpected_error(self) -> str:
        raise RuntimeError("private-token-should-not-leak")

    @strawberry.field
    def worker_thread(self, info: Info[RequestContext, None]) -> bool:
        request = info.context.request
        assert request is not None
        return threading.get_ident() != int(request.state.event_loop_thread)


@pytest.mark.parametrize(
    ("query", "code"),
    [("serviceError", "VALIDATION_FAILED"), ("unexpectedError", "INTERNAL_ERROR")],
)
def test_graphql_errors_are_safe_http_200(
    query: str, code: str, caplog: pytest.LogCaptureFixture
) -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    app = create_app(container=container, schema=SafeSchema(query=ProbeQuery))
    with TestClient(app) as client:
        result = client.post("/graphql", json={"query": "{ " + query + " }"})
    assert result.status_code == 200
    assert result.json()["errors"][0]["extensions"]["code"] == code
    assert "private-token-should-not-leak" not in result.text
    assert "private-token-should-not-leak" not in caplog.text


def test_invalid_bearer_is_safe_graphql_auth_error() -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    with TestClient(create_app(container=container)) as client:
        result = client.post(
            "/graphql",
            json={"query": "{ __typename }"},
            headers={"Authorization": "Bearer fabricated"},
        )
    assert result.status_code == 200
    assert result.json()["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"


def test_sync_resolver_runs_in_worker_thread() -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    app = create_app(container=container, schema=SafeSchema(query=ProbeQuery))

    @app.middleware("http")
    async def capture_thread(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.event_loop_thread = threading.get_ident()
        return await call_next(request)

    with TestClient(app) as client:
        result = client.post("/graphql", json={"query": "{ workerThread }"})
    assert result.json()["data"]["workerThread"] is True


@pytest.mark.parametrize("header", ["1aa370e9-7d2a-4ce7-ad0a-37f4277de503", "invalid-request-id"])
def test_request_id_echoes_valid_uuid_or_replaces_invalid_input(header: str) -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    with TestClient(create_app(container=container)) as client:
        result = client.post(
            "/graphql", json={"query": "{ __typename }"}, headers={"X-Request-Id": header}
        )
    response_id = result.headers["X-Request-Id"]
    assert str(UUID(response_id)) == response_id
    assert (response_id == header) == (header != "invalid-request-id")


def test_pre_execution_error_is_safe_and_has_request_id(caplog: pytest.LogCaptureFixture) -> None:
    def broken_factory(session: Session) -> SessionVerifier:
        raise RuntimeError("private-connection-credential")

    container = AppContainer(
        Config("unused", "fixture"),
        session_factory=Session,
        session_verifier_factory=broken_factory,
    )
    with TestClient(create_app(container=container)) as client:
        result = client.post("/graphql", json={"query": "{ __typename }"})
    assert result.status_code == 200
    assert result.json()["errors"][0]["extensions"]["code"] == "INTERNAL_ERROR"
    assert result.headers["X-Request-Id"]
    assert "private-connection-credential" not in result.text + caplog.text


@pytest.mark.parametrize("query", ["{", "{ missingField }"])
def test_pre_execution_graphql_syntax_and_schema_errors_use_400(query: str) -> None:
    container = AppContainer(Config("unused", "fixture"), session_factory=Session)
    with TestClient(create_app(container=container)) as client:
        response = client.post("/graphql", json={"query": query})
    assert response.status_code == 400
    assert response.json()["errors"]
