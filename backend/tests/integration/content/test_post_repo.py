from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import event, insert, select
from sqlalchemy.orm import Session
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.dataaccess.schema import (
    collection_items,
    collections,
    likes,
    media_assets,
    post_images,
    posts,
    user_blocks,
)
from tomateto.domain.content.paging import PageRequest

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def test_feed_filters_before_limit_and_keyset_no_duplicates(session: Session) -> None:
    session.execute(
        insert(posts),
        [
            {"id": i, "user_id": 3, "dish_id": 1, "created_at": NOW, "updated_at": NOW}
            for i in range(1, 31)
        ],
    )
    session.execute(
        insert(posts),
        [
            {"id": i, "user_id": 2, "dish_id": 1, "created_at": NOW, "updated_at": NOW}
            for i in range(100, 141)
        ],
    )
    session.execute(
        insert(posts).values(id=200, user_id=3, dish_id=1, is_hidden=True, created_at=NOW)
    )
    session.execute(insert(user_blocks).values(blocker_id=2, blocked_id=1))
    repo = PostRepository(session)
    seen: list[int] = []
    cursor = None
    while True:
        result = repo.list_feed("LATEST", PageRequest(10, cursor), 1)
        seen.extend(i.id for i in result.items)
        if not result.has_next_page:
            break
        assert len(result.items) == 10
        cursor = result.end_cursor
    assert seen == list(range(30, 0, -1))
    assert repo.list_by_author(2, PageRequest(), 1).items == ()
    assert repo.list_feed("LATEST", PageRequest(), 1, blocked_user_ids=[3]).items == ()
    assert len(repo.list_feed("LATEST", PageRequest(100), None).items) == 50
    assert all(
        item.is_saved is None for item in repo.list_feed("LATEST", PageRequest(), None).items
    )


def test_feed_batch_hydration_single_statement(session: Session) -> None:
    session.execute(insert(posts).values(id=1, user_id=3, dish_id=1, created_at=NOW))
    for position in range(2):
        asset = uuid4()
        session.execute(
            insert(media_assets).values(
                id=asset,
                owner_id=3,
                purpose="POST",
                state="ATTACHED",
                provider="fixture",
                storage_key=str(asset),
                url="/private/fixture",
                input_size_bytes=1,
                stored_size_bytes=1,
                mime_type="image/png",
                width=1,
                height=1,
                created_at=NOW,
                expires_at=datetime(2031, 1, 1, tzinfo=UTC),
                consumed_at=NOW,
            )
        )
        session.execute(insert(post_images).values(post_id=1, media_id=asset, position=position))
    session.execute(insert(likes), [{"post_id": 1, "user_id": 1}, {"post_id": 1, "user_id": 2}])
    session.execute(
        insert(collections),
        [
            {"id": 1, "user_id": 1, "name": "One", "name_normalized": "one"},
            {"id": 2, "user_id": 1, "name": "Two", "name_normalized": "two"},
        ],
    )
    session.execute(
        insert(collection_items),
        [{"collection_id": 1, "post_id": 1}, {"collection_id": 2, "post_id": 1}],
    )
    statements = []
    connection = session.connection()

    def count(*args: Any) -> None:
        statements.append(args[2])

    event.listen(connection, "before_cursor_execute", count)
    try:
        page = PostRepository(session).list_feed("LATEST", PageRequest(), 1)
    finally:
        event.remove(connection, "before_cursor_execute", count)
    assert len(statements) == 1 and len(page.items) == 1
    item = page.items[0]
    assert item.like_count == 2 and item.is_liked and item.is_saved and len(item.images) == 2


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_page_size(value: object) -> None:
    with pytest.raises(ValueError, match="PAGE_SIZE_INVALID"):
        PageRequest(cast(int, value))


def test_repository_returns_detached_record_and_caller_controls_rollback(session: Session) -> None:
    session.execute(insert(posts).values(id=1, user_id=1, dish_id=1))
    repo = PostRepository(session)
    post = repo.find_by_id(1, for_update=True)
    assert post is not None
    assert post.id == 1 and not hasattr(post, "_sa_instance_state")
    repo.delete(1)
    assert repo.find_by_id(1) is None
    assert session.in_transaction()


def test_feed_plan_uses_existing_index_without_forcing_planner(session: Session) -> None:
    import json

    from sqlalchemy import text
    from tomateto.dataaccess.content.post_repo import FEED_SQL

    session.execute(
        text(
            "INSERT INTO posts(id,user_id,dish_id,created_at,updated_at) "
            "SELECT i,3,1,'2030-01-01T00:00Z','2030-01-01T00:00Z' "
            "FROM generate_series(1,5000) i"
        )
    )
    session.execute(text("ANALYZE posts"))
    plan = session.execute(
        text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + FEED_SQL),
        {
            "viewer_id": None,
            "first": 10,
            "after_time": None,
            "after_id": None,
            "author_id": None,
            "blocked_user_ids": [],
        },
    ).scalar_one()
    assert "ix_posts_feed" in json.dumps(plan)


def test_save_update_and_replace_images_roundtrip(session: Session) -> None:
    from tomateto.dataaccess.content.media_upload_repo import MediaUploadRepository
    from tomateto.domain.content.records import PostImageRecord

    from db.testing import asset_record

    session.execute(insert(posts).values(id=50, user_id=1, dish_id=1))
    repo = PostRepository(session)
    template = repo.find_by_id(50)
    assert template is not None
    created = repo.save(replace(template, id=0, caption="created"))
    assert created.id != 50 and created.caption == "created"
    updated = repo.update(replace(created, caption="updated"))
    stored = repo.find_by_id(updated.id)
    assert stored is not None and stored.caption == "updated"
    asset = MediaUploadRepository(session).create(asset_record(state="ATTACHED", consumed_at=NOW))
    repo.replace_images(
        created.id, [PostImageRecord(id=0, post_id=created.id, media_id=asset.id, position=0)]
    )
    linked = session.execute(select(post_images).where(post_images.c.post_id == created.id)).all()
    assert len(linked) == 1
    repo.replace_images(created.id, [])
    assert (
        session.execute(select(post_images).where(post_images.c.post_id == created.id)).first()
        is None
    )
    stored_asset = MediaUploadRepository(session).find_by_id(asset.id)
    assert stored_asset is not None and stored_asset.state == "ATTACHED"
