"""Detached data returned by repositories; no Session or lazy loader escapes."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PostRecord:
    id: int
    user_id: int
    dish_id: int
    restaurant_id: int | None
    caption: str | None
    feeling: str | None
    location_name: str | None
    location_address: str | None
    latitude: float | None
    longitude: float | None
    price_range: str | None
    recipe_ingredients: list[str]
    recipe_steps: list[str]
    is_hidden: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PostImageRecord:
    id: int
    post_id: int
    media_id: UUID
    position: int


@dataclass(frozen=True)
class MediaAssetRecord:
    id: UUID
    owner_id: int
    purpose: str
    state: str
    provider: str
    storage_key: str
    url: str
    input_size_bytes: int
    stored_size_bytes: int
    mime_type: str
    width: int
    height: int
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None
    deleted_at: datetime | None


@dataclass(frozen=True)
class DishRecord:
    id: int
    name: str
    name_normalized: str
    is_seed: bool
    created_at: datetime


@dataclass(frozen=True)
class RestaurantRecord:
    id: int
    name: str
    name_normalized: str
    address: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime


@dataclass(frozen=True)
class MediaCleanupJobRecord:
    id: int
    media_id: UUID
    created_at: datetime
    next_attempt_at: datetime
    attempts: int
    completed_at: datetime | None
    last_error_code: str | None
