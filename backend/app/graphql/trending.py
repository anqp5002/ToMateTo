"""GraphQL query for the published dish trending connection."""

import strawberry
from strawberry.types import Info

from app.core.pagination import PageRequest
from app.graphql.context import RequestContext
from app.graphql.types import Cursor, Dish, PageInfo, PageInput
from app.services.trending_service import TrendingService


@strawberry.type
class TrendingEdge:
    cursor: Cursor
    node: Dish


@strawberry.type
class TrendingConnection:
    state: str
    edges: list[TrendingEdge]
    page_info: PageInfo


@strawberry.type
class TrendingQuery:
    @strawberry.field
    def trending(
        self, info: Info[RequestContext, None], page: PageInput | None = None
    ) -> TrendingConnection:
        request = (
            PageRequest.of(page.first, str(page.after) if page.after is not None else None)
            if page is not None
            else PageRequest.of()
        )
        principal = info.context.principal
        result = TrendingService(info.context.scope.session, info.context.clock).get_trending(
            request, principal.user_id if principal else None
        )
        return TrendingConnection(
            state=result.state,
            edges=[
                TrendingEdge(
                    cursor=Cursor(edge.cursor),
                    node=Dish(id=strawberry.ID(str(edge.node.dish_id)), name=edge.node.name),
                )
                for edge in result.connection.edges
            ],
            page_info=PageInfo(
                end_cursor=(
                    Cursor(result.connection.page_info.end_cursor)
                    if result.connection.page_info.end_cursor is not None
                    else None
                ),
                has_next_page=result.connection.page_info.has_next_page,
            ),
        )
