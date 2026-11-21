"""LATEST query service bridges S8 records with BE's versioned opaque cursor contract."""

from sqlalchemy.orm import Session

from tomateto.business.content.contracts import invalid
from tomateto.dataaccess.content.post_projection import PostProjection, PostView
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.domain.content.paging import PageRequest as RepositoryPageRequest
from tomateto.domain.content.paging import PostCursor
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
        after = None
        if page.after:
            cursor = self.codec.decode(page.after, "LATEST", scope=scope)
            if not isinstance(cursor, LatestCursor) or cursor.item_id <= 0:
                raise invalid("page.after", "CURSOR_INVALID")
            after = PostCursor(cursor.created_at, cursor.item_id)
        request = RepositoryPageRequest(page.first, after)
        repo = PostRepository(self.session)
        result = (
            repo.list_by_author(author_id, request, viewer)
            if author_id is not None
            else repo.list_feed("LATEST", request, viewer)
        )
        views = PostProjection(self.session).read([item.id for item in result.items], viewer)
        return RepositoryPage(
            [
                Edge(
                    self.codec.encode_latest(item.created_at, item.id, scope=scope), views[item.id]
                )
                for item in result.items
                if item.id in views
            ],
            result.has_next_page,
        )

    def get_post(self, post_id: int, principal: Principal | None) -> PostView:
        record = PostRepository(self.session).find_by_id(post_id)
        if record is None:
            raise DomainError("NOT_FOUND")
        viewer = principal.user_id if principal else None
        view = PostProjection(self.session).read([post_id], viewer).get(post_id)
        if view is None:
            raise DomainError("NOT_AVAILABLE")
        return view
