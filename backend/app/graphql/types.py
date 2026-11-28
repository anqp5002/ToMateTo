"""Shared GraphQL types used by the discovery and assistant operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, NewType

import strawberry

if TYPE_CHECKING:
    Cursor = NewType("Cursor", str)
else:
    Cursor = strawberry.scalar(
        NewType("Cursor", str), name="Cursor", serialize=str, parse_value=str
    )


@strawberry.input
class PageInput:
    first: int | None = 10
    after: Cursor | None = None


@strawberry.type
class PageInfo:
    end_cursor: Cursor | None
    has_next_page: bool


@strawberry.type
class Dish:
    id: strawberry.ID
    name: str


@strawberry.type
class Restaurant:
    id: strawberry.ID
    name: str
    address: str | None
    latitude: float | None
    longitude: float | None


@strawberry.enum
class PriceRange(Enum):
    UNDER_50K = "UNDER_50K"
    FROM_50K_TO_100K = "FROM_50K_TO_100K"
    FROM_100K_TO_200K = "FROM_100K_TO_200K"
    ABOVE_200K = "ABOVE_200K"


@strawberry.type
class User:
    id: strawberry.ID
    display_name: str
    avatar_url: str | None


@strawberry.type
class PostImage:
    id: strawberry.ID
    url: str
    position: int


@strawberry.type
class Recipe:
    ingredients: list[str] | None
    instructions: list[str] | None


@strawberry.type
class Post:
    id: strawberry.ID
    dish_name: str
    caption: str | None
    images: list[PostImage]
    author: User
    price_range: PriceRange | None
    address: str | None
    restaurant: Restaurant | None
    recipe: Recipe | None
    feeling: str | None
    latitude: float | None
    longitude: float | None
    like_count: int
    is_liked_by_viewer: bool | None
    is_saved_by_viewer: bool | None
    created_at: datetime
    updated_at: datetime
