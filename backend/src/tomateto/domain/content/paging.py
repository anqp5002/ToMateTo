"""Internal paging values, independent of the pending shared API cursor codec."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PostCursor:
    created_at: datetime
    id: int

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None or self.id <= 0:
            raise ValueError("Cursor needs an aware timestamp and positive ID")


@dataclass(frozen=True)
class PageRequest:
    first: int = 10
    after: PostCursor | None = None

    def __post_init__(self) -> None:
        if type(self.first) is not int or self.first < 1:
            raise ValueError("PAGE_SIZE_INVALID")

    @property
    def effective_first(self) -> int:
        return min(self.first, 50)


@dataclass(frozen=True)
class FeedItem:
    id: int
    user_id: int
    dish_id: int
    dish_name: str
    caption: str | None
    created_at: datetime
    updated_at: datetime
    like_count: int
    is_liked: bool | None
    is_saved: bool | None
    images: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class PageResult:
    items: tuple[FeedItem, ...]
    has_next_page: bool
    end_cursor: PostCursor | None
