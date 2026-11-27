"""Content input contracts; public API null values preserve scalar fields on update."""

from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from tomateto.shared.exceptions import AuthorizationError, FieldError, ValidationError
from tomateto.shared.identity import Principal

Price = Literal["UNDER_50K", "FROM_50K_TO_100K", "FROM_100K_TO_200K", "ABOVE_200K"]


class ImageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_id: int | None = None
    upload_id: UUID | None = None
    position: int


class RecipeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ingredients: list[str] | None = None
    instructions: list[str] | None = None


class PostInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dish_name: str | None = None
    caption: str | None = None
    restaurant_id: int | None = None
    restaurant_name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_range: Price | None = None
    feeling: str | None = None
    recipe: RecipeInput | None = None
    images: list[ImageInput] | None = None


MAX_BIGINT = 9_223_372_036_854_775_807


def invalid(field: str, code: str = "INVALID_VALUE") -> ValidationError:
    return ValidationError(field_errors=[FieldError(field, code, "Invalid input")])


def validate_bigint(value: int, field: str) -> None:
    """Ensure integer identifiers fit PostgreSQL signed BIGINT (>= 1)."""
    if type(value) is not int or not (1 <= value <= MAX_BIGINT):
        raise invalid(field)


class WritePolicy(Protocol):
    def authorize_write(
        self, principal: Principal | None, action: str, owner_id: int | None = None
    ) -> int: ...


class ContentWritePolicy:
    """Minimum fail-closed owner rules; injectable B10 port, not a replacement JWT verifier."""

    def authorize_write(
        self, principal: Principal | None, action: str, owner_id: int | None = None
    ) -> int:
        if principal is None:
            raise AuthorizationError("UNAUTHENTICATED")
        if owner_id is not None and owner_id != principal.user_id:
            raise AuthorizationError(
                "FORBIDDEN", field_errors=[FieldError("id", "OWNER_REQUIRED", "Owner required")]
            )
        return principal.user_id


class MediaStorage(Protocol):
    def store(self, key: str, content: bytes) -> None: ...
    def remove(self, key: str) -> None: ...


class TimeSource(Protocol):
    def now(self) -> datetime: ...
