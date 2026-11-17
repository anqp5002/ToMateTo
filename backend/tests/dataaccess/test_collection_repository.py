"""Test `CollectionRepository` (điểm nối 5 `createDefault`) trên PostgreSQL thật.

Bao: PK đôi T15, partial unique `uq_collections_one_default`, UNIQUE tên theo
chủ, FK CASCADE, con trỏ `(added_at DESC, post_id DESC)` không trùng/thiếu.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app._stubs.pagination import PageRequest
from app.dataaccess.social.collection_repository import (
    DEFAULT_COLLECTION_NAME,
    CollectionRepository,
    normalize_name,
)
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.support.factories import insert_post, insert_user


def _insert_item(session: Session, *, collection_id: int, post_id: int, added_at: datetime) -> None:
    """Chèn thẳng `collection_items` để điều khiển `added_at` (con trỏ cần mốc giờ)."""
    session.execute(
        text(
            "INSERT INTO collection_items (collection_id, post_id, added_at)"
            " VALUES (:collection_id, :post_id, :added_at)"
        ),
        {"collection_id": collection_id, "post_id": post_id, "added_at": added_at},
    )


def test_create_default_makes_one_saved_collection(db_session: Session) -> None:
    """Điểm nối 5: tạo một bộ `is_default=true` tên "Đã lưu", không đụng bộ khác."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    other = repository.create(user_id, "Món cuối tuần")

    created = repository.create_default(user_id)

    assert created.is_default is True
    assert created.name == DEFAULT_COLLECTION_NAME
    assert created.name_normalized == normalize_name(DEFAULT_COLLECTION_NAME)
    assert other.is_default is False  # không đổi cờ bộ khác
    assert repository.find_owner_id(created.id) == user_id
    assert repository.find_default(user_id) is not None


def test_create_default_twice_in_two_transactions_hits_partial_unique(
    db_session: Session,
) -> None:
    """Gọi lần hai ở transaction khác → `IntegrityError` từ partial unique, không nuốt."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    collection_id = CollectionRepository(db_session).create_default(user_id).id
    db_session.commit()  # kết thúc savepoint đầu, dữ liệu vẫn trong transaction của test

    second = CollectionRepository(db_session)
    with pytest.raises(IntegrityError):
        second.create_default(user_id)
    db_session.rollback()

    default_count = db_session.scalar(
        text("SELECT count(*) FROM collections WHERE user_id = :user_id AND is_default"),
        {"user_id": user_id},
    )
    assert default_count == 1
    assert collection_id > 0


def test_partial_unique_allows_many_non_default(db_session: Session) -> None:
    """Bộ không mặc định không bị partial unique chặn; bộ mặc định bị chặn."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    repository.create(user_id, "Bộ một")
    repository.create(user_id, "Bộ hai")
    repository.create_default(user_id)

    with pytest.raises(IntegrityError):
        repository.create_default(user_id)
    db_session.rollback()


def test_duplicate_name_in_same_owner_rejected(db_session: Session) -> None:
    """UNIQUE `(user_id, name_normalized)`: hai bộ cùng tên một chủ bị chặn.

    Cùng tên gõ khác dấu vẫn trùng sau chuẩn hoá Q01.
    """
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    repository.create(user_id, "Quán ngon")

    with pytest.raises(IntegrityError):
        repository.create(user_id, "  quán NGON ")
    db_session.rollback()


def test_exists_name_ignores_case_and_accents(db_session: Session) -> None:
    """`exists_name` so sau chuẩn hoá; `exclude_id` bỏ qua chính bộ đang sửa."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    collection = repository.create(user_id, "Đồ ngọt")

    assert repository.exists_name(user_id, "do ngot") is True
    assert repository.exists_name(user_id, "do ngot", exclude_id=collection.id) is False
    assert repository.exists_name(user_id, "Món mặn") is False


def test_pk_duplicated_item_is_noop(db_session: Session) -> None:
    """PK đôi T15: thêm cùng bài hai lần không sinh dòng thứ hai."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    post_id = insert_post(connection, user_id=user_id)
    repository = CollectionRepository(db_session)
    collection = repository.create_default(user_id)

    repository.add_item(collection.id, post_id)
    repository.add_item(collection.id, post_id)

    assert repository.count_items(collection.id) == 1
    repository.remove_item(collection.id, post_id)
    repository.remove_item(collection.id, post_id)  # lần hai là no-op
    assert repository.count_items(collection.id) == 0


def test_cascade_deletes_items_with_collection(db_session: Session) -> None:
    """FK CASCADE T15: xoá bộ thì bài trong bộ biến mất theo."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    post_id = insert_post(connection, user_id=user_id)
    repository = CollectionRepository(db_session)
    collection = repository.create_default(user_id)
    repository.add_item(collection.id, post_id)

    repository.delete(collection.id)
    db_session.flush()

    assert repository.find_by_id(collection.id) is None
    remaining = db_session.scalar(
        text("SELECT count(*) FROM collection_items WHERE collection_id = :id"),
        {"id": collection.id},
    )
    assert remaining == 0


def test_list_items_paginates_without_gaps_on_equal_timestamps(
    db_session: Session,
) -> None:
    """Con trỏ `(added_at DESC, post_id DESC)`: cùng `added_at` vẫn không trùng/thiếu."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    collection = repository.create_default(user_id)
    same_instant = datetime(2026, 11, 17, 9, 0, 0, tzinfo=UTC)
    post_ids = [insert_post(connection, user_id=user_id) for _ in range(5)]
    for post_id in post_ids:
        _insert_item(
            db_session,
            collection_id=collection.id,
            post_id=post_id,
            added_at=same_instant,
        )

    seen: list[int] = []
    cursor: str | None = None
    while True:
        page = repository.list_items(collection.id, PageRequest(first=2, after=cursor))
        seen.extend(item.post_id for item in page.items)
        if not page.has_next_page:
            assert page.end_cursor is None
            break
        cursor = page.end_cursor

    assert sorted(seen) == sorted(post_ids)
    assert len(seen) == len(set(seen))
    assert seen == sorted(post_ids, reverse=True)  # added_at bằng nhau → post_id DESC


def test_list_items_skips_hidden_and_blocked_authors(db_session: Session) -> None:
    """Bài ẩn và bài của người bị chặn không lọt vào trang (O6 lọc hai chiều)."""
    connection = db_session.connection()
    viewer = insert_user(connection)
    blocked = insert_user(connection)
    visible_author = insert_user(connection)
    repository = CollectionRepository(db_session)
    collection = repository.create_default(viewer)

    visible_post = insert_post(connection, user_id=visible_author)
    hidden_post = insert_post(connection, user_id=visible_author, is_hidden=True)
    blocked_post = insert_post(connection, user_id=blocked)
    base = datetime(2026, 11, 17, 9, 0, 0, tzinfo=UTC)
    for index, post_id in enumerate((visible_post, hidden_post, blocked_post)):
        _insert_item(
            db_session,
            collection_id=collection.id,
            post_id=post_id,
            added_at=base + timedelta(seconds=index),
        )
    repository.add_item(collection.id, visible_post)

    page = repository.list_items(
        collection.id, PageRequest.default(), viewer_id=viewer, blocked_user_ids=(blocked,)
    )

    assert [item.post_id for item in page.items] == [visible_post]


def test_saved_by_user_spans_all_collections(db_session: Session) -> None:
    """`saved_by_user` gom mọi bộ của người xem; khách trả rỗng."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    stranger = insert_user(connection)
    repository = CollectionRepository(db_session)
    default = repository.create_default(user_id)
    custom = repository.create(user_id, "Món chay")
    first = insert_post(connection, user_id=stranger)
    second = insert_post(connection, user_id=stranger)
    repository.add_item(default.id, first)
    repository.add_item(custom.id, second)

    assert repository.saved_by_user(user_id, [first, second]) == {first, second}
    assert repository.saved_by_user(None, [first, second]) == set()


def test_list_by_user_paginates_and_can_rename(db_session: Session) -> None:
    """Danh sách bộ mới nhất trước, con trỏ chạy hết; đổi tên cập nhật tên chuẩn hoá."""
    connection = db_session.connection()
    user_id = insert_user(connection)
    repository = CollectionRepository(db_session)
    repository.create_default(user_id)
    for name in ("Bộ A", "Bộ B"):
        repository.create(user_id, name)

    seen: list[int] = []
    cursor: str | None = None
    while True:
        page = repository.list_by_user(user_id, PageRequest(first=2, after=cursor))
        seen.extend(item.id for item in page.items)
        if not page.has_next_page:
            break
        cursor = page.end_cursor
    assert len(seen) == 3
    assert len(set(seen)) == 3

    target = repository.create(user_id, "Tên cũ")
    repository.rename(target.id, "Tên mới")
    renamed = repository.find_by_id(target.id)
    assert renamed is not None
    assert renamed.name == "Tên mới"
    assert renamed.name_normalized == normalize_name("Tên mới")
