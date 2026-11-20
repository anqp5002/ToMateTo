"""Verify the fixture and a selective nearby read against the committed schema."""

from collections.abc import Iterator
from typing import Any

from app.core.database import create_database_engine
from app.models.base import Base
from app.repositories.search_repo import NEARBY_CANDIDATES_SQL, nearby_parameters
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable


def _plan_nodes(plan: dict[str, Any]) -> Iterator[dict[str, Any]]:
    yield plan
    for child in plan.get("Plans", []):
        yield from _plan_nodes(child)


def test_discovery_metadata_has_its_models_and_no_partial_external_tables() -> None:
    assert {
        "chat_sessions",
        "chat_messages",
        "trending_runs",
        "trending_post_snapshots",
        "trending_dish_snapshots",
        "trending_tag_snapshots",
    } <= set(Base.metadata.tables)
    dependencies = {
        "chat_sessions": "users",
        "trending_post_snapshots": "posts",
        "trending_dish_snapshots": "dishes",
        "trending_tag_snapshots": "tags",
    }
    for target in dependencies.values():
        table = Base.metadata.tables.get(target)
        assert table is None or len(table.columns) > 1
    engine = create_database_engine("postgresql+psycopg://example.invalid/test")
    try:
        for table_name, target in dependencies.items():
            ddl = CreateTable(Base.metadata.tables[table_name]).compile(dialect=engine.dialect)
            assert f"REFERENCES {target} (id)" in str(ddl)
    finally:
        engine.dispose()


def test_fixture_covers_the_s8_data_contract(db_session: Session) -> None:
    assert db_session.scalar(text("SELECT count(*) FROM posts")) == 200
    assert db_session.scalar(text("SELECT count(DISTINCT post_id) FROM post_images")) == 30
    assert db_session.scalar(text("SELECT count(*) FROM dishes")) == 100
    assert db_session.scalar(text("SELECT count(*) FROM restaurants")) == 60


def test_selective_nearby_plan_can_use_coordinate_index(db_session: Session) -> None:
    # A tiny catalog may correctly use Seq Scan. Add distant rows to exercise the
    # intended index under a selective geographic filter, without disabling scans.
    db_session.execute(
        text("""
            INSERT INTO restaurants(id,name,name_normalized,latitude,longitude)
            SELECT i,'Far '||i,'far '||i,-30+(i%10),-60+(i%10)
            FROM generate_series(1001,6000) i
        """)
    )
    db_session.execute(text("ANALYZE restaurants"))
    plan = db_session.scalar(
        text("EXPLAIN (FORMAT JSON) " + NEARBY_CANDIDATES_SQL),
        nearby_parameters(21.0285, 105.8542, 5000),
    )
    assert plan
    nodes = list(_plan_nodes(plan[0]["Plan"]))
    assert any(
        node.get("Index Name") == "ix_restaurants_coordinates"
        and node["Node Type"] in {"Index Scan", "Index Only Scan", "Bitmap Index Scan"}
        for node in nodes
    ), plan
    assert not any(
        node["Node Type"] == "Seq Scan" and node.get("Relation Name") == "restaurants"
        for node in nodes
    ), plan
