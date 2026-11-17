"""`collection_repository` — đọc/ghi T14 `collections` + T15 `collection_items`.

Chữ ký theo 6.1-A BE dòng 710-723; **không commit** (SPEC r2 §4 điểm nối 5).

`create_default` là điểm nối 5: tạo đúng một bộ "Đã lưu" `is_default=true`
trong transaction của người gọi (thường transaction đăng ký), không đổi cờ bộ
khác. Lần gọi thứ hai ở transaction khác bị partial unique
`uq_collections_one_default` chặn bằng `IntegrityError` — lỗi **nổi lên**, không
nuốt (SPEC r2 §4, Giả thuyết: service S9 bắt lỗi rồi trả bộ cũ).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app._stubs.pagination import CursorCodec, PageRequest
from app.domain.social._reference_tables import posts_table
from app.domain.social.collection import Collection
from app.domain.social.collection_item import CollectionItem

#: Tên hiển thị của bộ mặc định (T14, 5.3-B).
DEFAULT_COLLECTION_NAME = "Đã lưu"

# Bảng `posts` thuộc T09 (ngoài phạm vi S8); chỉ cần `id`, `user_id`, `is_hidden`
# để lọc bài ẩn và bài của người bị chặn.
_posts = posts_table


def normalize_name(name: str) -> str:
    """Chuẩn hoá tên bộ theo Q01: chữ thường, bỏ dấu, gộp khoảng trắng.

    Dùng cho `name_normalized` (khoá UNIQUE theo chủ). Không dùng cho email.
    """
    decomposed = unicodedata.normalize("NFD", name)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # "đ" không tách được bằng NFD nên đổi tay sau khi bỏ dấu.
    without_marks = without_marks.replace("đ", "d").replace("Đ", "D")
    return " ".join(without_marks.casefold().split())


@dataclass(frozen=True, slots=True)
class CollectionPage:
    """Một trang danh sách; `end_cursor=None` khi hết dữ liệu."""

    items: list[Collection]
    end_cursor: str | None
    has_next_page: bool


@dataclass(frozen=True, slots=True)
class CollectionItemPage:
    """Một trang bài trong bộ; con trỏ theo `(added_at, post_id)`."""

    items: list[CollectionItem]
    end_cursor: str | None
    has_next_page: bool


def _page_cursor(
    rows: list[CollectionItem], request: PageRequest
) -> tuple[list[CollectionItem], str | None, bool]:
    """Cắt `first+1` dòng thành trang + `hasNextPage` + `endCursor`."""
    has_next = len(rows) > request.first
    page = rows[: request.first]
    if not page or not has_next:
        return page, None, has_next
    last = page[-1]
    return page, CursorCodec.encode(last.added_at, last.post_id), has_next


class CollectionRepository:
    """Truy vấn bộ sưu tập; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------ ghi

    def create_default(self, user_id: int) -> Collection:
        """Tạo bộ "Đã lưu" mặc định cho `user_id`; không commit, không đổi cờ khác.

        `flush()` để ràng buộc partial unique được kiểm ngay tại đây: gọi lần
        hai trong transaction khác sẽ ném `IntegrityError` cho người gọi.
        """
        collection = Collection(
            user_id=user_id,
            name=DEFAULT_COLLECTION_NAME,
            name_normalized=normalize_name(DEFAULT_COLLECTION_NAME),
            is_default=True,
        )
        self._session.add(collection)
        self._session.flush()
        return collection

    def create(self, user_id: int, name: str) -> Collection:
        """Tạo bộ thường (`is_default=false`); tên trùng trong chủ → IntegrityError."""
        collection = Collection(
            user_id=user_id,
            name=name,
            name_normalized=normalize_name(name),
            is_default=False,
        )
        self._session.add(collection)
        self._session.flush()
        return collection

    def rename(self, collection_id: int, name: str) -> None:
        """Đổi tên bộ; không đụng cờ `is_default`."""
        self._session.execute(
            update(Collection)
            .where(Collection.id == collection_id)
            .values(name=name, name_normalized=normalize_name(name))
        )
        self._session.flush()

    def delete(self, collection_id: int) -> None:
        """Xoá bộ; `collection_items` xoá theo nhờ FK CASCADE."""
        self._session.execute(delete(Collection).where(Collection.id == collection_id))
        self._session.flush()

    def add_item(self, collection_id: int, post_id: int) -> None:
        """Thêm bài vào bộ; thêm lặp lại là no-op (PK đôi + ON CONFLICT)."""
        self._session.execute(
            insert(CollectionItem)
            .values(collection_id=collection_id, post_id=post_id)
            .on_conflict_do_nothing(
                index_elements=[CollectionItem.collection_id, CollectionItem.post_id]
            )
        )

    def remove_item(self, collection_id: int, post_id: int) -> None:
        """Bỏ bài khỏi bộ; bài không có trong bộ là no-op."""
        self._session.execute(
            delete(CollectionItem).where(
                CollectionItem.collection_id == collection_id,
                CollectionItem.post_id == post_id,
            )
        )

    # ----------------------------------------------------------------- đọc

    def find_by_id(self, collection_id: int) -> Collection | None:
        """Bộ theo mã, không phân biệt chủ (service kiểm quyền)."""
        return self._session.get(Collection, collection_id)

    def find_owner_id(self, collection_id: int) -> int | None:
        """Mã chủ của bộ, `None` nếu bộ không tồn tại (dùng cho assertOwner)."""
        return self._session.scalar(
            select(Collection.user_id).where(Collection.id == collection_id)
        )

    def find_default(self, user_id: int) -> Collection | None:
        """Bộ mặc định của một chủ, `None` nếu chưa tạo."""
        return self._session.scalar(
            select(Collection).where(Collection.user_id == user_id, Collection.is_default.is_(True))
        )

    def exists_name(self, user_id: int, name: str, *, exclude_id: int | None = None) -> bool:
        """Chủ đã có bộ trùng tên (sau chuẩn hoá) chưa; `exclude_id` để bỏ qua chính nó."""
        conditions = [
            Collection.user_id == user_id,
            Collection.name_normalized == normalize_name(name),
        ]
        if exclude_id is not None:
            conditions.append(Collection.id != exclude_id)
        return bool(self._session.scalar(select(exists().where(*conditions))))

    def list_by_user(self, user_id: int, page: PageRequest) -> CollectionPage:
        """Bộ của một chủ, mới nhất trước, con trỏ `(created_at, id)`."""
        stmt = (
            select(Collection)
            .where(Collection.user_id == user_id)
            .order_by(Collection.created_at.desc(), Collection.id.desc())
            .limit(page.first + 1)
        )
        if page.after is not None:
            payload = CursorCodec.decode(page.after)
            stmt = stmt.where(
                (Collection.created_at < payload.created_at)
                | ((Collection.created_at == payload.created_at) & (Collection.id < payload.id))
            )
        rows = list(self._session.scalars(stmt).all())
        has_next = len(rows) > page.first
        items = rows[: page.first]
        end_cursor = (
            CursorCodec.encode(items[-1].created_at, items[-1].id) if items and has_next else None
        )
        return CollectionPage(items=items, end_cursor=end_cursor, has_next_page=has_next)

    def list_items(
        self,
        collection_id: int,
        page: PageRequest,
        viewer_id: int | None = None,
        blocked_user_ids: tuple[int, ...] | list[int] = (),
    ) -> CollectionItemPage:
        """Bài trong bộ, mới thêm trước, con trỏ `(added_at DESC, post_id DESC)`.

        Bỏ bài bị ẩn và bài của người nằm trong `blocked_user_ids` (O6: lọc hai
        chiều do service tổng hợp). Hai bài cùng `added_at` vẫn phân trang đúng
        nhờ `id` thứ hai trong khoá sắp — đây là yêu cầu của `ix_collection_items_cursor`.
        """
        # Chỉ lấy bài đang hiển thị; khách (viewer_id=None) không áp bộ lọc chặn.
        visible_posts = select(_posts.c.id).where(_posts.c.is_hidden.is_(False))
        if viewer_id is not None and blocked_user_ids:
            visible_posts = visible_posts.where(_posts.c.user_id.not_in(list(blocked_user_ids)))
        stmt = (
            select(CollectionItem)
            .where(
                CollectionItem.collection_id == collection_id,
                CollectionItem.post_id.in_(visible_posts),
            )
            .order_by(CollectionItem.added_at.desc(), CollectionItem.post_id.desc())
            .limit(page.first + 1)
        )
        if page.after is not None:
            payload = CursorCodec.decode(page.after)
            stmt = stmt.where(
                (CollectionItem.added_at < payload.created_at)
                | (
                    (CollectionItem.added_at == payload.created_at)
                    & (CollectionItem.post_id < payload.id)
                )
            )
        rows = list(self._session.scalars(stmt).all())
        items, end_cursor, has_next = _page_cursor(rows, page)
        return CollectionItemPage(items=items, end_cursor=end_cursor, has_next_page=has_next)

    def saved_by_user(self, viewer_id: int | None, post_ids: list[int]) -> set[int]:
        """Tập con `post_ids` đã lưu trong **bất kỳ** bộ nào của người xem."""
        if viewer_id is None or not post_ids:
            return set()
        rows = self._session.execute(
            select(CollectionItem.post_id).where(
                CollectionItem.post_id.in_(post_ids),
                CollectionItem.collection_id.in_(
                    select(Collection.id).where(Collection.user_id == viewer_id)
                ),
            )
        ).all()
        return {post_id for (post_id,) in rows}

    def count_items(self, collection_id: int) -> int:
        """Số bài trong bộ (dùng cho test và hiển thị số đếm)."""
        total = self._session.scalar(
            select(func.count())
            .select_from(CollectionItem)
            .where(CollectionItem.collection_id == collection_id)
        )
        return int(total or 0)
