"""Search query validation and service boundary."""

from dataclasses import dataclass
from typing import Protocol
from unicodedata import normalize

from app.core.exceptions import FieldError, SystemError, ValidationError
from app.core.pagination import Edge, PageRequest, RepositoryPage
from app.repositories.search_details import SearchDetails
from app.repositories.search_repo import SearchHit, SearchKind

MAX_REFILL_ROUNDS = 100


class SearchReader(Protocol):
    def search(
        self,
        query: str,
        page: PageRequest,
        viewer_id: int | None = None,
        *,
        type_filter: SearchKind | None = None,
    ) -> RepositoryPage[SearchHit]: ...


class SearchDetailsReader(Protocol):
    def load(self, result: RepositoryPage[SearchHit], viewer_id: int | None) -> SearchDetails: ...


@dataclass(frozen=True)
class SearchPage:
    result: RepositoryPage[SearchHit]
    details: SearchDetails


class DiscoverySearchService:
    def __init__(self, reader: SearchReader, details: SearchDetailsReader) -> None:
        self._reader = reader
        self._details = details

    def search(
        self,
        query: str,
        page: PageRequest,
        viewer_id: int | None,
        *,
        type_filter: SearchKind | None = None,
    ) -> SearchPage:
        query = normalize("NFC", query).strip()
        if len(query) < 2:
            message = "Vui lòng nhập ít nhất 2 ký tự để tìm kiếm."
            raise ValidationError(field_errors=[FieldError("query", "", message)])
        return self._collect_visible(query, page, viewer_id, type_filter)

    def _collect_visible(
        self,
        query: str,
        page: PageRequest,
        viewer_id: int | None,
        type_filter: SearchKind | None,
    ) -> SearchPage:
        """Refill after concurrent hide/delete/block without returning an unusable cursor."""
        edges: list[Edge[SearchHit]] = []
        restaurants: list[dict[str, object]] = []
        posts: list[dict[str, object]] = []
        images: list[dict[str, object]] = []
        after = page.after
        # In a continuously changing dataset, fail safely rather than returning
        # an empty page that claims there is more but gives no cursor.
        for _ in range(MAX_REFILL_ROUNDS):
            batch = self._reader.search(
                query, PageRequest.of(page.first, after), viewer_id, type_filter=type_filter
            )
            details = self._details.load(batch, viewer_id)
            allowed_restaurants = {row["id"] for row in details.restaurants}
            allowed_posts = {row["id"] for row in details.posts}
            valid = [
                edge
                for edge in batch.edges
                if edge.node.kind == "DISH"
                or (edge.node.kind == "RESTAURANT" and edge.node.item_id in allowed_restaurants)
                or (edge.node.kind == "POST" and edge.node.item_id in allowed_posts)
            ]
            edges.extend(valid)
            restaurants.extend(details.restaurants)
            posts.extend(details.posts)
            images.extend(details.images)
            if len(edges) > page.first or not batch.has_next:
                break
            if batch.next_cursor is None or batch.next_cursor == after:
                raise SystemError()
            after = batch.next_cursor
        else:
            raise SystemError()

        return SearchPage(
            RepositoryPage(edges[: page.first], len(edges) > page.first),
            SearchDetails(restaurants, posts, images, viewer_id),
        )
