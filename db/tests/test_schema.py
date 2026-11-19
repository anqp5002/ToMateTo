import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine, create_engine, inspect, text
from tomateto.dataaccess.content.models import (
    Dish,
    MediaAsset,
    MediaCleanupJob,
    Post,
    PostImage,
    Restaurant,
)
from tomateto.dataaccess.schema import metadata

from db.scripts.verify_schema import verify_schema


def test_schema_contract(engine: Engine) -> None:
    assert verify_schema(engine) == {
        "tables": 25,
        "columns": 161,
        "constraints": 116,
        "indexes": 70,
    }
    for cls in (Post, PostImage, MediaAsset, Dish, Restaurant, MediaCleanupJob):
        assert cls.__table__.metadata is metadata
    with engine.connect() as connection:
        flags = connection.execute(
            text(
                "SELECT condeferrable,condeferred FROM pg_constraint "
                "WHERE conname='uq_post_images_post_id_position'"
            )
        ).one()
        assert tuple(flags) == (True, False)
        predicate = connection.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname='uq_collections_one_default'")
        ).scalar_one()
        assert "UNIQUE" in predicate and "is_default = true" in predicate


def test_model_catalog_drift(engine: Engine) -> None:
    with engine.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "compare_server_default": True}
        )
        assert compare_metadata(context, metadata) == []


def test_upgrade_downgrade_upgrade_uses_separate_database(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "tomateto_migration_" + uuid.uuid4().hex + "_test"
    admin = create_engine(engine.url, isolation_level="AUTOCOMMIT")
    temporary = create_engine(engine.url.set(database=name))
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        monkeypatch.setenv("DATABASE_URL", temporary.url.render_as_string(hide_password=False))
        config = Config(str(Path("db/alembic.ini").resolve()))
        command.upgrade(config, "head")
        assert verify_schema(temporary)["tables"] == 25
        command.downgrade(config, "base")
        assert inspect(temporary).get_table_names() == ["alembic_version"]
        with temporary.connect() as connection:
            assert (
                connection.execute(text("SELECT count(*) FROM alembic_version")).scalar_one() == 0
            )
            assert (
                connection.execute(
                    text(
                        "SELECT count(*) FROM pg_type t JOIN pg_namespace n "
                        "ON n.oid=t.typnamespace WHERE n.nspname='public' AND t.typtype='e'"
                    )
                ).scalar_one()
                == 0
            )
        command.upgrade(config, "head")
        assert verify_schema(temporary)["indexes"] == 70
    finally:
        temporary.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}"')
        admin.dispose()
