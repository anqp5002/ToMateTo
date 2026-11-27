"""Content-only schema component, intended for composition with the other groups."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TypeVar

import strawberry
from pydantic import ValidationError as InputValidationError
from sqlalchemy.orm import Session
from strawberry.types import Info

from tomateto.business.content.contracts import PostInput, TimeSource, WritePolicy, invalid
from tomateto.business.content.feed_service import FeedQueryService
from tomateto.business.content.post_service import PostLifecycleService
from tomateto.dataaccess.content.post_projection import PostView
from tomateto.presentation.errors import ErrorMapper
from tomateto.shared.exceptions import DomainError, FieldError, ValidationError
from tomateto.shared.identity import Principal
from tomateto.shared.pagination import PageRequest, RepositoryPage

T = TypeVar("T")


def mapped(action: Callable[[], T]) -> T:
    try:
        return action()
    except Exception as error:
        raise ErrorMapper().to_graphql_error(error) from None


@dataclass
class ContentContext:
    session: Session
    principal: Principal | None
    policy: WritePolicy
    clock: TimeSource
    identity_error: DomainError | None = None

    def verify(self) -> None:
        if self.identity_error:
            raise self.identity_error


@strawberry.enum
class FeedMode(StrEnum):
    LATEST = "LATEST"
    TRENDING = "TRENDING"


@strawberry.enum
class PriceRange(StrEnum):
    UNDER_50K = "UNDER_50K"
    FROM_50K_TO_100K = "FROM_50K_TO_100K"
    FROM_100K_TO_200K = "FROM_100K_TO_200K"
    ABOVE_200K = "ABOVE_200K"


@strawberry.input
class PageInput:
    first: int | None = None
    after: str | None = None


@strawberry.input
class PostImageInput:
    position: int
    image_id: strawberry.ID | None = None
    upload_id: strawberry.ID | None = None


@strawberry.input
class RecipeInput:
    ingredients: list[str] | None = None
    instructions: list[str] | None = None


@strawberry.input(name="CreatePostInput")
class CreateInput:
    dish_name: str
    caption: str | None = None
    images: list[PostImageInput] | None = None
    restaurant_id: strawberry.ID | None = None
    restaurant_name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_range: PriceRange | None = None
    feeling: str | None = None
    recipe: RecipeInput | None = None


@strawberry.type
class PublicUser:
    id: strawberry.ID
    display_name: str | None
    avatar_url: str | None


@strawberry.type
class PostImage:
    id: strawberry.ID
    url: str
    position: int


@strawberry.type
class Restaurant:
    id: strawberry.ID
    name: str
    address: str | None
    latitude: float | None
    longitude: float | None


@strawberry.type
class Recipe:
    ingredients: list[str]
    instructions: list[str]


@strawberry.type
class Post:
    id: strawberry.ID
    dish_name: str
    caption: str | None
    images: list[PostImage]
    author: PublicUser
    price_range: PriceRange | None
    address: str | None
    restaurant: Restaurant | None
    recipe: Recipe
    feeling: str | None
    latitude: float | None
    longitude: float | None
    like_count: int
    is_liked_by_viewer: bool | None
    is_saved_by_viewer: bool | None
    created_at: datetime
    updated_at: datetime


def post_type(view: PostView) -> Post:
    restaurant = None
    if view.restaurant_id is not None and view.restaurant_name is not None:
        restaurant = Restaurant(
            id=strawberry.ID(str(view.restaurant_id)),
            name=view.restaurant_name,
            address=view.restaurant_address,
            latitude=view.restaurant_latitude,
            longitude=view.restaurant_longitude,
        )
    return Post(
        id=strawberry.ID(str(view.id)),
        dish_name=view.dish_name,
        caption=view.caption,
        images=[
            PostImage(id=strawberry.ID(str(i.id)), url=i.url, position=i.position)
            for i in view.images
        ],
        author=PublicUser(
            id=strawberry.ID(str(view.user_id)),
            display_name=view.author_name,
            avatar_url=view.avatar_url,
        ),
        price_range=PriceRange(view.price_range) if view.price_range else None,
        address=view.address,
        restaurant=restaurant,
        recipe=Recipe(ingredients=view.ingredients, instructions=view.instructions),
        feeling=view.feeling,
        latitude=view.latitude,
        longitude=view.longitude,
        like_count=view.like_count,
        is_liked_by_viewer=view.is_liked,
        is_saved_by_viewer=view.is_saved,
        created_at=view.created_at,
        updated_at=view.updated_at,
    )


@strawberry.type
class PageInfo:
    end_cursor: str | None
    has_next_page: bool


@strawberry.type
class PostEdge:
    cursor: str
    node: Post


@strawberry.type
class PostConnection:
    edges: list[PostEdge]
    page_info: PageInfo


def connection(page: RepositoryPage[PostView]) -> PostConnection:
    return PostConnection(
        edges=[PostEdge(cursor=edge.cursor, node=post_type(edge.node)) for edge in page.edges],
        page_info=PageInfo(end_cursor=page.next_cursor, has_next_page=page.has_next),
    )


def request_page(page: PageInput | None) -> PageRequest:
    return PageRequest.of(page.first, page.after) if page else PageRequest()


_MAX_BIGINT = 9_223_372_036_854_775_807


def _camel_case(segment: str | int) -> str:
    if isinstance(segment, int):
        return str(segment)
    parts = segment.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)


def input_value(value: CreateInput) -> PostInput:
    try:
        return PostInput.model_validate(strawberry.asdict(value))
    except InputValidationError as exc:
        field_errors = [
            FieldError(
                field=".".join(_camel_case(part) for part in err["loc"]) or "input",
                code="INVALID_VALUE",
                message="Invalid input",
            )
            for err in exc.errors()
        ]
        raise ValidationError(field_errors=field_errors) from None


@strawberry.type
class Query:
    @strawberry.field
    def feed(
        self, info: Info[ContentContext, None], mode: FeedMode, page: PageInput | None = None
    ) -> PostConnection:
        def execute() -> PostConnection:
            ctx = info.context
            ctx.verify()
            if mode != FeedMode.LATEST:
                raise DomainError("INTEGRATION_UNAVAILABLE")
            return connection(
                FeedQueryService(ctx.session).latest(request_page(page), ctx.principal)
            )

        return mapped(execute)

    @strawberry.field
    def post(self, info: Info[ContentContext, None], id: strawberry.ID) -> Post | None:
        def execute() -> Post | None:
            ctx = info.context
            ctx.verify()
            try:
                post_id = int(id)
            except ValueError:
                raise invalid("id") from None
            if not (1 <= post_id <= _MAX_BIGINT):
                raise invalid("id")
            return post_type(FeedQueryService(ctx.session).get_post(post_id, ctx.principal))

        return mapped(execute)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_post(self, info: Info[ContentContext, None], input: CreateInput) -> Post:
        def execute() -> Post:
            ctx = info.context
            ctx.verify()
            saved = PostLifecycleService(ctx.session, ctx.policy, ctx.clock).create_post(
                ctx.principal, input_value(input)
            )
            return post_type(FeedQueryService(ctx.session).get_post(saved.id, ctx.principal))

        return mapped(execute)


schema = strawberry.Schema(query=Query, mutation=Mutation)
