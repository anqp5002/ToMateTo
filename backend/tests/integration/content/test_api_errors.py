"""Tests for API error mapping, validation, BIGINT bounds, media path safety, and CORS parsing."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import strawberry
from fastapi.testclient import TestClient
from sqlalchemy import insert
from sqlalchemy.orm import Session
from tomateto.bootstrap.content_app import create_app
from tomateto.bootstrap.run_content import _parse_cors_origins
from tomateto.dataaccess.schema import media_assets
from tomateto.presentation.content_graphql import CreateInput, PostImageInput, input_value
from tomateto.shared.exceptions import ValidationError
from tomateto.shared.identity import Principal


class _OwnerVerifier:
    def verify_session(self, raw_token: str) -> Principal:
        return Principal(1, "fixture-jti", 0)


@pytest.fixture
def client(session: Session, tmp_path: Path) -> Iterator[TestClient]:
    connection = session.connection()
    app = create_app(
        lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
        storage_root=tmp_path,
        verifier_factory=lambda _: _OwnerVerifier(),
    )
    with TestClient(app) as value:
        yield value


def test_graphql_request_validation_error_returns_400_with_request_id(client: TestClient) -> None:
    response = client.post("/graphql", json={})
    assert response.status_code == 400
    assert response.headers["x-request-id"]
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_FAILED"

    bad_json = client.post(
        "/graphql",
        content=b"{not-json",
        headers={"content-type": "application/json"},
    )
    assert bad_json.status_code == 400
    assert bad_json.headers["x-request-id"]
    assert bad_json.json()["error"]["code"] == "VALIDATION_FAILED"


def test_input_value_maps_pydantic_errors_to_camel_case_field_errors() -> None:
    payload = CreateInput(
        dish_name="Phở bò",
        images=[PostImageInput(position=0, upload_id=strawberry.ID("not-a-uuid"))],
        restaurant_id=strawberry.ID("not-an-int"),
    )
    with pytest.raises(ValidationError) as exc_info:
        input_value(payload)
    fields = {err.field: err.code for err in exc_info.value.field_errors}
    assert fields == {
        "images.0.uploadId": "INVALID_VALUE",
        "restaurantId": "INVALID_VALUE",
    }


@pytest.mark.parametrize("bad_id", ["abc", "0", "-1", "9223372036854775808"])
def test_post_query_rejects_non_numeric_or_out_of_bigint_id(
    client: TestClient, bad_id: str
) -> None:
    response = client.post(
        "/graphql",
        json={"query": "query($id: ID!) { post(id: $id) { id } }", "variables": {"id": bad_id}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"post": None}
    assert len(body["errors"]) == 1
    assert body["errors"][0]["extensions"] == {
        "code": "VALIDATION_FAILED",
        "fieldErrors": [{"field": "id", "code": "INVALID_VALUE", "message": "Invalid input"}],
    }


def test_media_route_returns_not_available_for_invalid_storage_key(
    client: TestClient, session: Session
) -> None:
    asset_id = uuid4()
    session.execute(
        insert(media_assets).values(
            id=asset_id,
            owner_id=1,
            purpose="POST",
            state="ATTACHED",
            provider="local",
            url=f"/media/{asset_id}",
            storage_key="../escape.png",
            input_size_bytes=10,
            stored_size_bytes=10,
            mime_type="image/png",
            width=1,
            height=1,
            created_at=datetime(2029, 12, 31, tzinfo=UTC),
            expires_at=datetime(2030, 1, 1, tzinfo=UTC),
            consumed_at=datetime(2029, 12, 31, tzinfo=UTC),
        )
    )
    session.flush()
    response = client.get(
        f"/media/{UUID(str(asset_id))}",
        headers={"Authorization": "Bearer test-a"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_AVAILABLE"


def test_parse_cors_origins_strips_whitespace_and_skips_empty() -> None:
    assert _parse_cors_origins(" http://localhost:7357 , , https://app.example.com  , ") == [
        "http://localhost:7357",
        "https://app.example.com",
    ]
    assert _parse_cors_origins("  ,  ") == []
