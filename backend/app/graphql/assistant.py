"""GraphQL operations for assistant conversations."""

from collections.abc import Callable
from datetime import datetime
from typing import cast

import strawberry
from strawberry.types import Info

from app.core.clock import Clock
from app.core.container import RequestScope
from app.core.exceptions import ValidationError
from app.core.pagination import PageRequest
from app.graphql.context import RequestContext
from app.graphql.types import Cursor, PageInfo, PageInput, Recipe
from app.models.chat import ChatMessage
from app.services.assistant_service import AssistantReplyData, AssistantService


@strawberry.input
class LocationInput:
    latitude: float
    longitude: float


@strawberry.input
class AskAssistantInput:
    message: str
    session_id: strawberry.ID | None = None
    location: LocationInput | None = None


@strawberry.input
class AssistantRetryInput:
    message_id: strawberry.ID


@strawberry.type
class AssistantDraft:
    dish_name: str | None
    caption: str | None
    recipe: Recipe | None
    restaurant_name: str | None


@strawberry.type
class AssistantMessage:
    id: strawberry.ID
    role: str
    content: str
    status: str
    created_at: datetime
    draft: AssistantDraft | None


@strawberry.type
class AssistantSession:
    id: strawberry.ID
    created_at: datetime
    last_message_at: datetime | None


@strawberry.type
class AssistantMessageEdge:
    cursor: Cursor
    node: AssistantMessage


@strawberry.type
class AssistantSessionEdge:
    cursor: Cursor
    node: AssistantSession


@strawberry.type
class AssistantMessageConnection:
    edges: list[AssistantMessageEdge]
    page_info: PageInfo


@strawberry.type
class AssistantSessionConnection:
    edges: list[AssistantSessionEdge]
    page_info: PageInfo


@strawberry.type
class AssistantReply:
    session_id: strawberry.ID
    message: AssistantMessage


def _id(value: strawberry.ID) -> int:
    try:
        parsed = int(value)
        if parsed <= 0:
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise ValidationError() from None


def _service(info: Info[RequestContext, None]) -> AssistantService:
    request = info.context.request
    if request is None:
        raise RuntimeError("Missing request context.")
    factory = cast("ServiceFactory", request.app.state.assistant_service_factory)
    return factory(info.context.scope, info.context.clock)


ServiceFactory = Callable[[RequestScope, Clock], AssistantService]


def _page(page: PageInput | None) -> PageRequest:
    return (
        PageRequest.of(page.first, str(page.after) if page and page.after is not None else None)
        if page
        else PageRequest.of()
    )


def _draft(data: dict[str, object] | None) -> AssistantDraft | None:
    """Project a stored draft to the GraphQL contract without exposing extra fields."""
    if data is None:
        return None

    dish_name = data.get("dishName")
    caption = data.get("caption")
    restaurant_name = data.get("restaurantName")
    if any(
        value is not None and not isinstance(value, str)
        for value in (dish_name, caption, restaurant_name)
    ):
        return None
    recipe_data = data.get("recipe")
    recipe = None
    if recipe_data is not None:
        if not isinstance(recipe_data, dict):
            return None
        ingredients = recipe_data.get("ingredients")
        instructions = recipe_data.get("instructions")
        for value in (ingredients, instructions):
            if value is not None and (
                not isinstance(value, list) or not all(isinstance(item, str) for item in value)
            ):
                return None
        recipe = Recipe(ingredients=ingredients, instructions=instructions)
    return AssistantDraft(
        dish_name=cast(str | None, dish_name),
        caption=cast(str | None, caption),
        recipe=recipe,
        restaurant_name=cast(str | None, restaurant_name),
    )


def _message(row: ChatMessage) -> AssistantMessage:
    return AssistantMessage(
        id=strawberry.ID(str(row.id)),
        role=row.role,
        content=row.content,
        status=row.status,
        created_at=row.created_at,
        draft=_draft(row.post_draft),
    )


def _reply(value: AssistantReplyData) -> AssistantReply:
    return AssistantReply(
        session_id=strawberry.ID(str(value.session_id)), message=_message(value.message)
    )


@strawberry.type
class AssistantQuery:
    @strawberry.field
    def assistant_sessions(
        self, info: Info[RequestContext, None], page: PageInput | None = None
    ) -> AssistantSessionConnection:
        result = _service(info).list_sessions(info.context.principal, _page(page))
        return AssistantSessionConnection(
            edges=[
                AssistantSessionEdge(
                    cursor=Cursor(e.cursor),
                    node=AssistantSession(
                        id=strawberry.ID(str(e.node.id)),
                        created_at=e.node.created_at,
                        last_message_at=e.node.last_message_at,
                    ),
                )
                for e in result.edges
            ],
            page_info=PageInfo(
                end_cursor=Cursor(result.next_cursor) if result.next_cursor else None,
                has_next_page=result.has_next,
            ),
        )

    @strawberry.field
    def assistant_history(
        self,
        info: Info[RequestContext, None],
        session_id: strawberry.ID | None = None,
        page: PageInput | None = None,
    ) -> AssistantMessageConnection:
        result = _service(info).history(
            _id(session_id) if session_id else None, info.context.principal, _page(page)
        )
        return AssistantMessageConnection(
            edges=[
                AssistantMessageEdge(cursor=Cursor(e.cursor), node=_message(e.node))
                for e in result.edges
            ],
            page_info=PageInfo(
                end_cursor=Cursor(result.next_cursor) if result.next_cursor else None,
                has_next_page=result.has_next,
            ),
        )


@strawberry.type
class AssistantMutation:
    @strawberry.mutation
    def ask_assistant(
        self, info: Info[RequestContext, None], input: AskAssistantInput
    ) -> AssistantReply:
        if input.location is not None and not (
            -90 <= input.location.latitude <= 90 and -180 <= input.location.longitude <= 180
        ):
            raise ValidationError()
        result = _service(info).ask(
            input.message,
            _id(input.session_id) if input.session_id else None,
            info.context.principal,
            (input.location.latitude, input.location.longitude) if input.location else None,
        )
        return _reply(result)

    @strawberry.mutation
    def retry_assistant(
        self, info: Info[RequestContext, None], input: AssistantRetryInput
    ) -> AssistantReply:
        return _reply(_service(info).retry(_id(input.message_id), info.context.principal))
