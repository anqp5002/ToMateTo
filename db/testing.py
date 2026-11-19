from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, insert, text
from sqlalchemy.orm import Session
from tomateto.dataaccess.schema import dishes, metadata, users
from tomateto.domain.content.records import MediaAssetRecord

from db.connection import make_engine, require_test_reset


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    require_test_reset()
    command.upgrade(Config(str(Path(__file__).parent / "alembic.ini")), "head")
    instance = make_engine()
    yield instance
    instance.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as connection:
        outer = connection.begin()
        value = Session(bind=connection, join_transaction_mode="create_savepoint")
        value.execute(users.update().values(avatar_media_id=None, cover_media_id=None))
        value.execute(text("DELETE FROM chat_messages WHERE role = 'assistant'"))
        for table in reversed(metadata.sorted_tables):
            value.execute(table.delete())
        value.execute(
            insert(users),
            [
                {
                    "id": i,
                    "email": f"u{i}@example.invalid",
                    "email_normalized": f"u{i}@example.invalid",
                    "password_hash": "fixture-only",
                    "display_name": f"User {i}",
                }
                for i in range(1, 5)
            ],
        )
        value.execute(insert(dishes).values(id=1, name="Phở bò", name_normalized="pho bo"))
        try:
            yield value
        finally:
            value.close()
            outer.rollback()


def asset_record(
    *,
    owner_id: int = 1,
    purpose: str = "POST",
    state: str = "PENDING",
    consumed_at: datetime | None = None,
) -> MediaAssetRecord:
    """A detached asset fixture; IDs/keys are unique for each test invocation."""
    now = datetime(2030, 1, 1, tzinfo=UTC)
    return MediaAssetRecord(
        id=uuid4(),
        owner_id=owner_id,
        purpose=purpose,
        state=state,
        provider="fixture",
        storage_key=str(uuid4()),
        url="/private/fixture",
        input_size_bytes=100,
        stored_size_bytes=80,
        mime_type="image/png",
        width=1,
        height=1,
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=1),
        consumed_at=consumed_at,
        deleted_at=None,
    )
