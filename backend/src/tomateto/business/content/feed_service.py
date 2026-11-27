"""LATEST query service bridges S8 records with BE's versioned opaque cursor contract."""

from sqlalchemy.orm import Session

from tomateto.business.content.contracts import invalid, validate_bigint
from tomateto.dataaccess.content.post_projection import PostProjection, PostView
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.shared.exceptions import DomainError
from tomateto.shared.identity import Principal
from tomateto.shared.pagination import CursorCodec, Edge, LatestCursor, PageRequest, RepositoryPage


class FeedQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.codec = CursorCodec()

    def latest(
        self, page: PageRequest, principal: Principal | None, author_id: int | None = None
    ) -> RepositoryPage[PostView]:
        viewer = principal.user_id if principal else None
        scope = f"content:{author_id}:{viewer}"
        after_time, after_id = None, None
        if page.after:
            cursor = self.codec.decode(page.after, "LATEST", scope=scope)
            if not isinstance(cursor, LatestCursor) or cursor.item_id <= 0:
                raise invalid("page.after", "CURSOR_INVALID")
            after_time, after_id = cursor.created_at, cursor.item_id
        projection = PostProjection(self.session)
        items, has_next_page = projection.list_latest_ids(
            page.first,
            viewer,
            author_id=author_id,
            after_time=after_time,
            after_id=after_id,
        )
        if not items:
            return RepositoryPage([], False)
        views = projection.read([post_id for post_id, _ in items], viewer)
        return RepositoryPage(
            [
                Edge(
                    self.codec.encode_latest(created_at, post_id, scope=scope),
                    views[post_id],
                )
                for post_id, created_at in items
                if post_id in views
            ],
            has_next_page,
        )

    def get_post(self, post_id: int, principal: Principal | None) -> PostView:
        validate_bigint(post_id, "id")
        record = PostRepository(self.session).find_by_id(post_id)
        if record is None:
            raise DomainError("NOT_FOUND")
        viewer = principal.user_id if principal else None
        view = PostProjection(self.session).read([post_id], viewer).get(post_id)
        if view is None:
            raise DomainError("NOT_AVAILABLE")
        return view
