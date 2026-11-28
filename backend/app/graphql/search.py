"""GraphQL search operation and its response shape."""

from enum import Enum

import strawberry
from strawberry.types import Info

from app.core.pagination import PageRequest
from app.graphql.context import RequestContext
from app.graphql.types import (
    Cursor,
    Dish,
    PageInfo,
    PageInput,
    Post,
    Restaurant,
)
from app.repositories.search_details import SearchDetailsRepository
from app.repositories.search_repo import SearchKind, SearchRepository
from app.services.discovery_search import DiscoverySearchService


@strawberry.enum
class SearchType(Enum):
    DISH = "DISH"
    RESTAURANT = "RESTAURANT"
    POST = "POST"


@strawberry.type
class SearchResult:
    type: SearchType
    dish: Dish | None = None
    restaurant: Restaurant | None = None
    post: Post | None = None


@strawberry.type
class SearchEdge:
    cursor: Cursor
    node: SearchResult


@strawberry.type
class SearchConnection:
    edges: list[SearchEdge]
    page_info: PageInfo


def _type_filter(value: SearchType | None) -> SearchKind | None:
    if value is SearchType.DISH:
        return "DISH"
    if value is SearchType.RESTAURANT:
        return "RESTAURANT"
    if value is SearchType.POST:
        return "POST"
    return None


@strawberry.type
class SearchQuery:
    @strawberry.field
    def search(
        self,
        info: Info[RequestContext, None],
        query: str,
        type: SearchType | None = None,
        page: PageInput | None = None,
    ) -> SearchConnection:
        scope = info.context.scope
        principal = info.context.principal
        requested = (
            PageRequest.of(page.first, str(page.after) if page.after is not None else None)
            if page
            else PageRequest.of()
        )
        result = DiscoverySearchService(
            SearchRepository(scope.session), SearchDetailsRepository(scope.session)
        ).search(
            query,
            requested,
            principal.user_id if principal else None,
            type_filter=_type_filter(type),
        )
        from app.graphql.search_mapper import map_search

        return map_search(result)
