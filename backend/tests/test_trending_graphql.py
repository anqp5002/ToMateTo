from datetime import UTC, datetime, timedelta
from decimal import Decimal

import strawberry
from app.core.config import Config
from app.core.container import AppContainer
from app.graphql.schema import SafeSchema
from app.graphql.trending import TrendingQuery
from app.main import create_app
from app.models.trending import TrendingRun
from app.repositories.trending_repo import SnapshotScore, TrendingSnapshotRepository
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker


def test_graphql_trending_waiting_and_ready(
    db_engine: Engine, session_factory: sessionmaker[Session]
) -> None:
    @strawberry.type
    class Query(TrendingQuery):
        pass

    container = AppContainer(Config("unused", "fixture"), session_factory=session_factory)
    client = TestClient(create_app(container=container, schema=SafeSchema(query=Query)))
    query = (
        "{ trending { state edges { cursor node { id name } } "
        "pageInfo { endCursor hasNextPage } } }"
    )
    try:
        with client:
            waiting = client.post("/graphql", json={"query": query})
            assert waiting.json()["data"]["trending"] == {
                "state": "WAITING",
                "edges": [],
                "pageInfo": {"endCursor": None, "hasNextPage": False},
            }
            now = datetime.now(UTC)
            with session_factory.begin() as session:
                TrendingSnapshotRepository(session).publish(
                    TrendingRun(
                        window_start=now - timedelta(days=7), window_end=now, formula_version="test"
                    ),
                    [SnapshotScore(1, Decimal(2))],
                    [SnapshotScore(1, Decimal(2))],
                )
            ready = client.post("/graphql", json={"query": query})
            assert ready.status_code == 200
            data = ready.json()["data"]["trending"]
            assert data["state"] == "READY"
            assert data["edges"][0]["node"] == {"id": "1", "name": "Phở 1"}
    finally:
        with db_engine.begin() as connection:
            connection.execute(text("DELETE FROM trending_runs"))
