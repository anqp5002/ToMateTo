import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from psycopg import Error as PsycopgError
from sqlalchemy import Engine, insert, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from tomateto.dataaccess.content.dish_repo import DishRepository
from tomateto.dataaccess.content.media_upload_repo import MediaUploadRepository, UploadRejectedError
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.dataaccess.schema import dishes, media_assets, posts, users
from tomateto.domain.content.records import DishRecord, MediaAssetRecord


def wait_for_database_lock(engine: Engine, pid: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            waiting = connection.execute(
                text("SELECT wait_event_type FROM pg_stat_activity WHERE pid=:pid"), {"pid": pid}
            ).scalar_one()
        if waiting == "Lock":
            return
        time.sleep(0.02)
    raise AssertionError("Second connection did not enter a real PostgreSQL lock wait")


def test_dish_upsert_two_real_transactions(engine: Engine) -> None:
    name = "Concurrent " + uuid4().hex
    first = Session(engine)
    first.begin()
    created = DishRepository(first).upsert(name)
    ready = threading.Event()
    state: dict[str, int] = {}

    def contender() -> DishRecord:
        with Session(engine) as second, second.begin():
            state["pid"] = second.execute(text("SELECT pg_backend_pid()")).scalar_one()
            ready.set()
            return DishRepository(second).upsert(name.upper())

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(contender)
            try:
                assert ready.wait(5)
                wait_for_database_lock(engine, state["pid"])
            finally:
                first.commit()  # Always release the winner's lock, including failed assertions.
            other = future.result(timeout=5)
        assert created.id == other.id and created.name_normalized == other.name_normalized
    finally:
        first.close()
        with engine.begin() as connection:
            connection.execute(dishes.delete().where(dishes.c.id == created.id))


def test_consume_race_rechecks_state_after_lock(engine: Engine) -> None:
    owner = int(uuid4().hex[:8], 16) + 10000
    asset_id = uuid4()
    now = datetime.now(UTC)
    with Session(engine) as setup, setup.begin():
        setup.execute(
            insert(users).values(
                id=owner,
                email=f"{owner}@example.invalid",
                email_normalized=f"{owner}@example.invalid",
                password_hash="fixture",
                display_name="Race",
            )
        )
        MediaUploadRepository(setup).create(
            MediaAssetRecord(
                id=asset_id,
                owner_id=owner,
                purpose="POST",
                state="PENDING",
                provider="fixture",
                storage_key=str(asset_id),
                url="/fixture",
                input_size_bytes=1,
                stored_size_bytes=1,
                mime_type="image/png",
                width=1,
                height=1,
                created_at=now - timedelta(minutes=1),
                expires_at=now + timedelta(hours=1),
                consumed_at=None,
                deleted_at=None,
            )
        )
    first = Session(engine)
    first.begin()
    MediaUploadRepository(first).consume(asset_id, owner, "POST", now)
    ready = threading.Event()
    state: dict[str, int] = {}

    def contender() -> str:
        try:
            with Session(engine) as second, second.begin():
                state["pid"] = second.execute(text("SELECT pg_backend_pid()")).scalar_one()
                ready.set()
                MediaUploadRepository(second).consume(asset_id, owner, "POST", now)
        except UploadRejectedError as error:
            return str(error)
        raise AssertionError("Second consumer unexpectedly succeeded")

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(contender)
            try:
                assert ready.wait(5)
                wait_for_database_lock(engine, state["pid"])
            finally:
                first.commit()
            assert future.result(timeout=5) == "STATE"
        with Session(engine) as reader:
            loaded = MediaUploadRepository(reader).find_by_id(asset_id)
            assert loaded is not None and loaded.state == "ATTACHED"
    finally:
        first.close()
        with engine.begin() as connection:
            connection.execute(media_assets.delete().where(media_assets.c.id == asset_id))
            connection.execute(users.delete().where(users.c.id == owner))


def test_find_by_id_for_update_locks_row(engine: Engine) -> None:
    identifier = int(uuid4().hex[:8], 16) + 10000
    with engine.begin() as connection:
        connection.execute(
            insert(users).values(
                id=identifier,
                email=f"{identifier}@example.invalid",
                email_normalized=f"{identifier}@example.invalid",
                password_hash="fixture",
                display_name="Lock",
            )
        )
        connection.execute(
            insert(dishes).values(
                id=identifier, name=str(identifier), name_normalized=str(identifier)
            )
        )
        connection.execute(
            insert(posts).values(id=identifier, user_id=identifier, dish_id=identifier)
        )
    try:
        with Session(engine) as first, first.begin():
            assert PostRepository(first).find_by_id(identifier, for_update=True) is not None
            with Session(engine) as second, second.begin():
                second.execute(text("SET LOCAL lock_timeout = '300ms'"))
                with pytest.raises(OperationalError) as failure:
                    PostRepository(second).find_by_id(identifier, for_update=True)
                assert isinstance(failure.value.orig, PsycopgError)
                assert failure.value.orig.sqlstate == "55P03"
                second.rollback()
    finally:
        with engine.begin() as connection:
            connection.execute(posts.delete().where(posts.c.id == identifier))
            connection.execute(dishes.delete().where(dishes.c.id == identifier))
            connection.execute(users.delete().where(users.c.id == identifier))
