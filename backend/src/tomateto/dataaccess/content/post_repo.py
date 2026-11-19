from pathlib import Path

from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.orm import Session

from tomateto.dataaccess.content.common import snapshot, values
from tomateto.dataaccess.schema import post_images, posts
from tomateto.domain.content.paging import FeedItem, PageRequest, PageResult, PostCursor
from tomateto.domain.content.records import PostImageRecord, PostRecord

FEED_SQL = Path(__file__).with_name("sql").joinpath("feed_latest.sql").read_text(encoding="utf-8")


class PostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_id(self, post_id: int, for_update: bool = False) -> PostRecord | None:
        statement = select(posts).where(posts.c.id == post_id)
        if for_update:
            statement = statement.with_for_update()
        row = self.session.execute(statement).mappings().first()
        return snapshot(PostRecord, row) if row else None

    def save(self, post: PostRecord) -> PostRecord:
        row = (
            self.session.execute(insert(posts).values(**values(post)).returning(posts))
            .mappings()
            .one()
        )
        return snapshot(PostRecord, row)

    def update(self, post: PostRecord) -> PostRecord:
        row = (
            self.session.execute(
                update(posts)
                .where(posts.c.id == post.id)
                .values(**values(post, include_id=False))
                .returning(posts)
            )
            .mappings()
            .one()
        )
        return snapshot(PostRecord, row)

    def delete(self, post_id: int) -> None:
        # Caller must authorize, lock, detach assets and enqueue jobs in the same transaction.
        self.session.execute(delete(posts).where(posts.c.id == post_id))

    def replace_images(self, post_id: int, images: list[PostImageRecord]) -> None:
        if any(image.post_id != post_id for image in images):
            raise ValueError("Image belongs to a different post")
        self.session.execute(delete(post_images).where(post_images.c.post_id == post_id))
        if images:
            self.session.execute(insert(post_images), [values(i) for i in images])

    def _page(
        self,
        page: PageRequest,
        viewer_id: int | None,
        author_id: int | None = None,
        blocked_user_ids: list[int] | None = None,
    ) -> PageResult:
        after = page.after
        rows = list(
            self.session.execute(
                text(FEED_SQL),
                {
                    "viewer_id": viewer_id,
                    "first": page.effective_first,
                    "after_time": after.created_at if after else None,
                    "after_id": after.id if after else None,
                    "author_id": author_id,
                    "blocked_user_ids": blocked_user_ids or [] if viewer_id is not None else [],
                },
            ).mappings()
        )
        items = tuple(
            FeedItem(
                **{
                    **dict(row),
                    "like_count": int(row["like_count"]),
                    "images": tuple(row["images"]),
                }
            )
            for row in rows[: page.effective_first]
        )
        cursor = PostCursor(items[-1].created_at, items[-1].id) if items else None
        return PageResult(items, len(rows) > page.effective_first, cursor)

    def list_feed(
        self,
        mode: str,
        page: PageRequest,
        viewer_id: int | None = None,
        blocked_user_ids: list[int] | None = None,
    ) -> PageResult:
        if mode != "LATEST":
            raise NotImplementedError("TRENDING is the S10 discovery integration")
        return self._page(page, viewer_id, blocked_user_ids=blocked_user_ids)

    def list_by_author(
        self, author_id: int, page: PageRequest, viewer_id: int | None = None
    ) -> PageResult:
        return self._page(page, viewer_id, author_id)
