from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.core.exceptions import ValidationError
from app.core.pagination import (
    CursorCodec,
    Edge,
    LatestCursor,
    PageMapper,
    PageRequest,
    RepositoryPage,
    SavedCursor,
    SearchCursor,
    TrendingCursor,
)


@pytest.mark.parametrize(("first", "expected"), [(None, 10), (1, 1), (10, 10), (50, 50), (51, 50)])
def test_tc_be_n0201_page_size(first: int | None, expected: int) -> None:
    assert PageRequest.of(first).first == expected


@pytest.mark.parametrize("first", [0, -1])
def test_nonpositive_first_has_page_field_error(first: int) -> None:
    with pytest.raises(ValidationError) as failure:
        PageRequest.of(first)
    assert failure.value.field_errors[0].code == "PAGE_SIZE_INVALID"


def test_cursor_round_trips_preserve_kind_scope_and_decimal() -> None:
    codec = CursorCodec()
    now = datetime(2026, 11, 18, tzinfo=UTC)
    assert codec.decode(codec.encode_latest(now, 9), "LATEST") == LatestCursor(now, 9)
    assert codec.decode(codec.encode_saved(now, 8), "SAVED") == SavedCursor(now, 8)
    score = Decimal("123456789.0000000000000000001")
    token = codec.encode_trending(7, score, 6, scope="dishes")
    assert codec.decode(token, "TRENDING", run_id=7, scope="dishes") == TrendingCursor(7, score, 6)
    with pytest.raises(ValidationError):
        codec.decode(token, "LATEST", scope="dishes")
    with pytest.raises(ValidationError):
        codec.decode(token, "TRENDING", run_id=8, scope="dishes")
    with pytest.raises(ValidationError):
        codec.decode(token, "TRENDING", scope="posts")


def test_search_cursor_is_tied_to_query_and_type_scope() -> None:
    codec = CursorCodec()
    token = codec.encode_search(3, 1, 7, scope="pho:DISH")
    assert codec.decode(token, "SEARCH", scope="pho:DISH") == SearchCursor(3, 1, 7)
    with pytest.raises(ValidationError):
        codec.decode(token, "SEARCH", scope="bun:DISH")
    with pytest.raises(ValidationError):
        codec.decode(token, "LATEST", scope="pho:DISH")


@pytest.mark.parametrize("cursor", ["", "bad-cursor", "bnVsbA==", "e30=", "!" * 20])
def test_malformed_cursors_are_validation_errors(cursor: str) -> None:
    with pytest.raises(ValidationError) as failure:
        CursorCodec().decode(cursor, "LATEST")
    assert failure.value.field_errors[0].code == "CURSOR_INVALID"


@pytest.mark.parametrize(
    ("items", "expected", "has_next"),
    [([], [], False), ([1], [1], False), ([1, 2], [1, 2], False), ([1, 2, 3], [1, 2], True)],
)
def test_mapper_uses_last_returned_row(
    items: list[int], expected: list[int], has_next: bool
) -> None:
    page = RepositoryPage.from_rows(items, PageRequest.of(2), str)
    result = PageMapper.to_connection(page, lambda item: item)
    assert [edge.node for edge in result.edges] == expected
    assert result.page_info.has_next_page is has_next
    assert result.page_info.end_cursor == (str(expected[-1]) if expected else None)


def test_mapper_uses_repository_cursors_and_has_next_for_already_sliced_page() -> None:
    page = RepositoryPage([Edge("db-cursor-one", 1), Edge("db-cursor-two", 2)], has_next=True)
    result = PageMapper.to_connection(page, str)
    assert result.edges == [Edge("db-cursor-one", "1"), Edge("db-cursor-two", "2")]
    assert result.page_info.end_cursor == "db-cursor-two"
    assert result.page_info.has_next_page
