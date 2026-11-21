"""Versioned, typed keyset cursors and Relay-style connection mapping."""

import base64
import binascii
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Generic, Literal, TypeVar

from tomateto.shared.exceptions import FieldError, ValidationError

CursorKind = Literal["LATEST", "SAVED", "TRENDING", "SEARCH"]
T = TypeVar("T")
U = TypeVar("U")


def _invalid_cursor() -> ValidationError:
    message = "Không thể tải trang tiếp. Vui lòng tải lại."
    return ValidationError(field_errors=[FieldError("page.after", "CURSOR_INVALID", message)])


@dataclass(frozen=True)
class PageRequest:
    first: int = 10
    after: str | None = None

    def __post_init__(self) -> None:
        if type(self.first) is not int or self.first <= 0:
            message = "Số lượng mục mỗi trang không hợp lệ."
            raise ValidationError(
                field_errors=[FieldError("page.first", "PAGE_SIZE_INVALID", message)]
            )
        object.__setattr__(self, "first", min(self.first, 50))

    @classmethod
    def of(cls, first: int | None = None, after: str | None = None) -> "PageRequest":
        return cls(10 if first is None else first, after)


@dataclass(frozen=True)
class LatestCursor:
    created_at: datetime
    item_id: int


@dataclass(frozen=True)
class SavedCursor:
    added_at: datetime
    post_id: int


@dataclass(frozen=True)
class TrendingCursor:
    run_id: int
    score: Decimal
    target_id: int


@dataclass(frozen=True)
class SearchCursor:
    relevance: int
    type_rank: int
    item_id: int


class CursorCodec:
    def encode_search(
        self, relevance: int, type_rank: int, item_id: int, *, scope: str = ""
    ) -> str:
        return self._encode("SEARCH", [relevance, type_rank, item_id], scope)

    def encode_latest(self, created_at: datetime, item_id: int, *, scope: str = "") -> str:
        self._validate_time(created_at)
        return self._encode("LATEST", [created_at.isoformat(), item_id], scope)

    def encode_saved(self, added_at: datetime, post_id: int, *, scope: str = "") -> str:
        self._validate_time(added_at)
        return self._encode("SAVED", [added_at.isoformat(), post_id], scope)

    def encode_trending(
        self, run_id: int, score: Decimal, target_id: int, *, scope: str = ""
    ) -> str:
        if not isinstance(score, Decimal) or not score.is_finite():
            raise _invalid_cursor()
        return self._encode("TRENDING", [run_id, str(score), target_id], scope)

    def decode(
        self,
        cursor: str,
        kind: CursorKind,
        *,
        run_id: int | None = None,
        scope: str = "",
    ) -> LatestCursor | SavedCursor | TrendingCursor | SearchCursor:
        try:
            if kind not in ("LATEST", "SAVED", "TRENDING", "SEARCH"):
                raise ValueError("Unsupported cursor kind.")
            if not cursor or len(cursor) > 4096:
                raise ValueError("Invalid size.")
            encoded = cursor.encode("ascii")
            decoded = base64.b64decode(encoded, altchars=b"-_", validate=True)
            payload = json.loads(decoded)
            if (
                not isinstance(payload, dict)
                or payload.get("v") != 1
                or payload.get("kind") != kind
                or payload.get("scope") != scope
            ):
                raise ValueError("Cursor context differs.")
            values = payload["key"]
            if not isinstance(values, list):
                raise ValueError("Missing key.")
            if kind == "SEARCH":
                if len(values) != 3 or not all(type(value) is int for value in values):
                    raise ValueError("Invalid search key.")
                if values[0] not in (1, 2, 3) or values[1] not in (1, 2, 3):
                    raise ValueError("Invalid search rank.")
                return SearchCursor(*values)
            if kind == "TRENDING":
                if len(values) != 3 or type(values[0]) is not int or type(values[2]) is not int:
                    raise ValueError("Invalid trending key.")
                if not isinstance(values[1], str):
                    raise ValueError("Decimal must be text.")
                score = Decimal(values[1])
                if not score.is_finite() or (run_id is not None and values[0] != run_id):
                    raise ValueError("Invalid score or run.")
                return TrendingCursor(values[0], score, values[2])
            if len(values) != 2 or not isinstance(values[0], str) or type(values[1]) is not int:
                raise ValueError("Invalid chronological key.")
            moment = datetime.fromisoformat(values[0])
            self._validate_time(moment)
            return (
                LatestCursor(moment, values[1])
                if kind == "LATEST"
                else SavedCursor(moment, values[1])
            )
        except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error, InvalidOperation):
            raise _invalid_cursor() from None

    @staticmethod
    def _validate_time(moment: datetime) -> None:
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise _invalid_cursor()

    @staticmethod
    def _encode(kind: CursorKind, values: list[object], scope: str) -> str:
        payload = {"v": 1, "kind": kind, "scope": scope, "key": values}
        return base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")


@dataclass(frozen=True)
class Edge(Generic[T]):
    cursor: str
    node: T


@dataclass(frozen=True)
class RepositoryPage(Generic[T]):
    edges: list[Edge[T]]
    has_next: bool

    @property
    def items(self) -> list[T]:
        return [edge.node for edge in self.edges]

    @property
    def next_cursor(self) -> str | None:
        return self.edges[-1].cursor if self.edges else None

    @classmethod
    def from_rows(
        cls, rows: Sequence[T], page: PageRequest, cursor_for: Callable[[T], str]
    ) -> "RepositoryPage[T]":
        """Turn a first+1 query result into a page with repository-owned cursors."""
        return cls(
            [Edge(cursor_for(row), row) for row in rows[: page.first]], len(rows) > page.first
        )


@dataclass(frozen=True)
class PageInfo:
    end_cursor: str | None
    has_next_page: bool


@dataclass(frozen=True)
class Connection(Generic[T]):
    edges: list[Edge[T]]
    page_info: PageInfo


class PageMapper:
    @staticmethod
    def to_connection(page: RepositoryPage[T], node_for: Callable[[T], U]) -> Connection[U]:
        edges = [Edge(edge.cursor, node_for(edge.node)) for edge in page.edges]
        return Connection(edges, PageInfo(page.next_cursor, page.has_next))
