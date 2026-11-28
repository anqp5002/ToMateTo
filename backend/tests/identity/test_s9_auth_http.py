import secrets
from collections.abc import Iterator
from typing import Any

import pytest
from app.dataaccess.social.collection_repository import CollectionRepository
from app.domain.identity.user import User
from app.domain.social.collection import Collection
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

REGISTER = (
    "mutation($input: RegisterInput!) { register(input: $input)"
    " { accessToken expiresInSeconds user { id displayName } } }"
)
LOGIN = "mutation($input: LoginInput!) { login(input: $input) { accessToken } }"
LOGOUT = "mutation { logout { success } }"


def execute(
    client: TestClient,
    query: str,
    input: dict[str, str] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/graphql",
        json={"query": query, "variables": {"input": input}},
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, db_connection: Connection) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", secrets.token_urlsafe(32))
    monkeypatch.setenv("OTP_PEPPER", secrets.token_urlsafe(32))
    with TestClient(app) as browser:
        app.state.session_factory = lambda: Session(
            bind=db_connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield browser


def test_auth_lifecycle(client: TestClient, db_connection: Connection) -> None:
    email = "User@example.test"
    password = secrets.token_urlsafe(12)
    credentials = {"email": email, "password": password}
    registration = {**credentials, "displayName": "Minh"}
    result = execute(client, REGISTER, registration)["data"]["register"]
    account_id = int(result["user"]["id"])
    assert result["expiresInSeconds"] == 604800
    assert db_connection.execute(
        select(Collection.id).where(Collection.user_id == account_id, Collection.is_default)
    ).scalar_one()
    duplicate = execute(client, REGISTER, {**registration, "email": email.lower()})
    assert duplicate["errors"][0]["extensions"]["code"] == "ALREADY_EXISTS"
    invalid = execute(client, REGISTER, {**registration, "password": ""})
    assert invalid["errors"][0]["extensions"]["fieldErrors"][0]["field"] == "password"
    unknown = execute(client, LOGIN, {**credentials, "email": "missing@example.test"})
    wrong = execute(client, LOGIN, {**credentials, "password": secrets.token_urlsafe(12)})
    assert unknown["errors"][0]["message"] == wrong["errors"][0]["message"]
    assert wrong["errors"][0]["extensions"]["detailCode"] == "LOGIN_FAILED"
    token = execute(client, LOGIN, credentials)["data"]["login"]["accessToken"]
    assert execute(client, "{ viewer { id } }", token=token)["data"]["viewer"]["id"] == str(
        account_id
    )
    assert execute(client, LOGOUT, token=token)["data"]["logout"]["success"]
    assert execute(client, LOGOUT, token=token)["data"]["logout"]["success"]
    assert (
        execute(client, "{ viewer { id } }", token=token)["errors"][0]["extensions"]["code"]
        == "UNAUTHENTICATED"
    )


def test_collection_failure_rolls_back_account(
    client: TestClient, db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: CollectionRepository, user_id: int) -> None:
        raise RuntimeError("Collection unavailable")

    monkeypatch.setattr(CollectionRepository, "create_default", fail)
    email = "rollback@example.test"
    result = execute(
        client,
        REGISTER,
        {"email": email, "password": secrets.token_urlsafe(12), "displayName": "Minh"},
    )
    assert result.get("errors")
    assert (
        db_connection.execute(
            select(User.id).where(User.email_normalized == email)
        ).scalar_one_or_none()
        is None
    )
