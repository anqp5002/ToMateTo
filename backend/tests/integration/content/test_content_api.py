"""HTTP/GraphQL integration against PostgreSQL, with a verifier injected only in tests."""

from collections.abc import Iterator
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from tomateto.bootstrap.content_app import create_app
from tomateto.dataaccess.schema import media_assets, posts, user_blocks, users
from tomateto.integration.media_storage import LocalMediaStorage
from tomateto.shared.exceptions import AuthorizationError
from tomateto.shared.identity import Principal


class Verifier:
    def verify_session(self, raw_token: str) -> Principal:
        if raw_token not in {"test-a", "test-b"}:
            raise AuthorizationError("UNAUTHENTICATED")
        return Principal(1 if raw_token == "test-a" else 2, "fixture-jti", 0)


class FrozenClock:
    def now(self) -> datetime:
        return datetime(2030, 1, 1, tzinfo=UTC)


@pytest.fixture
def client(session: Session, tmp_path: Path) -> Iterator[TestClient]:
    connection = session.connection()
    app = create_app(
        lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
        storage_root=tmp_path,
        verifier_factory=lambda _: Verifier(),
        clock=FrozenClock(),
    )
    with TestClient(app) as value:
        yield value


def png(width: int = 20, height: int = 10) -> bytes:
    target = BytesIO()
    Image.new("RGB", (width, height), "red").save(target, format="PNG")
    return target.getvalue()


def create(client: TestClient, name: str = "Phở bò", **extra: object) -> dict[str, object]:
    response = client.post(
        "/graphql",
        headers={"Authorization": "Bearer test-a"},
        json={
            "query": """mutation($input:CreatePostInput!){createPost(input:$input){id dishName
          caption images{id url position} author{id displayName} createdAt}}""",
            "variables": {"input": {"dishName": name, **extra}},
        },
    )
    return response.json()  # type: ignore[no-any-return]


def test_upload_and_create_are_atomic(client: TestClient, session: Session) -> None:
    result = client.post(
        "/media/uploads",
        headers={"Authorization": "Bearer test-a"},
        data={"purpose": "POST"},
        files={"file": ("ignored.txt", png(2000, 1000))},
    )
    assert result.status_code == 201
    upload = result.json()
    assert (upload["width"], upload["height"]) == (1600, 800)
    assert upload["expiresAt"].startswith("2030-01-02")
    assert client.get(upload["url"]).status_code == 404  # PENDING is owner-only
    before = session.scalar(select(func.count()).select_from(posts))
    invalid = create(
        client,
        images=[
            {"uploadId": upload["uploadId"], "position": 0},
            {"uploadId": "00000000-0000-0000-0000-000000000001", "position": 1},
        ],
    )
    assert invalid["errors"]
    assert session.scalar(select(func.count()).select_from(posts)) == before
    state = session.scalar(
        select(media_assets.c.state).where(media_assets.c.id == UUID(upload["uploadId"]))
    )
    assert state == "PENDING"
    valid = create(client, images=[{"uploadId": upload["uploadId"], "position": 0}])
    assert "errors" not in valid
    assert client.get(upload["url"]).status_code == 200
    assert client.get(upload["url"]).headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize(
    ("content", "code"), [(b"not-image", 400), (b"x" * (10 * 1024 * 1024 + 1), 413)]
)
def test_upload_rejects_invalid_bytes(client: TestClient, content: bytes, code: int) -> None:
    response = client.post(
        "/media/uploads",
        headers={"Authorization": "Bearer test-a"},
        data={"purpose": "POST"},
        files={"file": ("photo.png", content)},
    )
    assert response.status_code == code
    assert response.headers["x-request-id"]


def test_upload_http_contract(client: TestClient) -> None:
    assert client.post("/media/uploads").status_code == 401
    assert client.post("/media/uploads", headers={"Authorization": "Bearer bad"}).status_code == 401
    assert (
        client.post(
            "/media/uploads", headers={"Authorization": "Bearer test-a"}, json={}
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/media/uploads",
            headers={"Authorization": "Bearer test-a"},
            files={"file": ("a.png", png())},
        ).status_code
        == 400
    )


def test_graphql_feed_cursor_and_public_privacy(client: TestClient, session: Session) -> None:
    for i in range(12):
        assert "errors" not in create(client, f"Món {i}")
    operation = """query($page:PageInput){feed(mode:LATEST,page:$page){edges{cursor node{
       id dishName author{id displayName avatarUrl} isLikedByViewer}}
       pageInfo{endCursor hasNextPage}}}"""
    first = client.post("/graphql", json={"query": operation}).json()["data"]["feed"]
    assert len(first["edges"]) == 10
    assert first["pageInfo"]["hasNextPage"]
    assert first["edges"][0]["node"]["author"]["displayName"] is None
    assert first["edges"][0]["node"]["isLikedByViewer"] is None
    second = client.post(
        "/graphql",
        json={"query": operation, "variables": {"page": {"after": first["pageInfo"]["endCursor"]}}},
    ).json()["data"]["feed"]
    assert len(second["edges"]) == 2
    assert not (
        {e["node"]["id"] for e in first["edges"]} & {e["node"]["id"] for e in second["edges"]}
    )
    for page in [{"first": 0}, {"after": "broken"}]:
        error = client.post(
            "/graphql", json={"query": operation, "variables": {"page": page}}
        ).json()["errors"][0]
        assert error["extensions"]["code"] == "VALIDATION_FAILED"
    limited = client.post(
        "/graphql", json={"query": operation, "variables": {"page": {"first": 100}}}
    ).json()["data"]["feed"]
    assert len(limited["edges"]) == 12
    post_id = first["edges"][0]["node"]["id"]
    session.execute(user_blocks.insert().values(blocker_id=1, blocked_id=2))
    result = client.post(
        "/graphql",
        headers={"Authorization": "Bearer test-b"},
        json={"query": f'{{post(id:"{post_id}"){{id}}}}'},
    ).json()
    assert result["errors"][0]["extensions"]["code"] == "NOT_AVAILABLE"
    session.execute(update(posts).values(is_hidden=True))
    assert client.post("/graphql", json={"query": operation}).json()["data"]["feed"]["edges"] == []
    assert session.scalar(select(func.count()).select_from(users)) == 4


def test_create_rejects_guest_and_empty_dish(client: TestClient) -> None:
    operation = 'mutation{createPost(input:{dishName:"Phở"}){id}}'
    guest = client.post("/graphql", json={"query": operation}).json()
    assert guest["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"
    assert create(client, " ")["errors"]


def test_default_verifier_rejects_tokens(session: Session, tmp_path: Path) -> None:
    connection = session.connection()
    with TestClient(
        create_app(
            lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
            storage_root=tmp_path,
        )
    ) as app:
        response = app.post(
            "/graphql",
            headers={"Authorization": "Bearer test-a"},
            json={"query": "{feed(mode:LATEST){edges{node{id}}}}"},
        ).json()
        assert response["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED"


def test_old_avatar_url_checks_current_visibility(client: TestClient, session: Session) -> None:
    uploaded = client.post(
        "/media/uploads",
        headers={"Authorization": "Bearer test-a"},
        data={"purpose": "AVATAR"},
        files={"file": ("a.png", png())},
    ).json()
    asset_id = UUID(uploaded["uploadId"])
    session.execute(
        update(media_assets)
        .where(media_assets.c.id == asset_id)
        .values(state="ATTACHED", consumed_at=FrozenClock().now())
    )
    session.execute(
        update(users)
        .where(users.c.id == 1)
        .values(avatar_media_id=asset_id, public_profile_fields=["avatarUrl"])
    )
    assert client.get(uploaded["url"]).status_code == 200
    session.execute(update(users).where(users.c.id == 1).values(public_profile_fields=[]))
    assert client.get(uploaded["url"]).status_code == 404


def test_storage_failure_preserves_other_flows(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(self: LocalMediaStorage, key: str, content: bytes) -> None:
        raise OSError("fixture storage outage")

    monkeypatch.setattr(LocalMediaStorage, "store", fail)
    response = client.post(
        "/media/uploads",
        headers={"Authorization": "Bearer test-a"},
        data={"purpose": "POST"},
        files={"file": ("a.png", png())},
    )
    assert response.status_code == 503
    assert "fixture" not in response.text
    assert "errors" not in create(client)
