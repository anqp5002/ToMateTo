from unicodedata import normalize

import pytest
from app.core.exceptions import ValidationError
from app.core.pagination import PageMapper, PageRequest
from app.repositories.search_repo import SearchRepository
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_repository_reads_seeded_catalog(db_session: Session) -> None:
    repo = SearchRepository(db_session)
    assert len(repo.search_dishes("", PageRequest.of(50)).items) == 50
    assert len(repo.search_restaurants("", PageRequest.of(50)).items) == 50
    assert len(repo.search_posts("", PageRequest.of(50), viewer_id=None).items) == 50


def test_nearby_returns_all_candidates_before_service_limit(db_session: Session) -> None:
    repo = SearchRepository(db_session)
    assert len(repo.find_nearby(21.0285, 105.8542, 5000)) >= 60


def test_search_cursor_is_stable_and_bound_to_query(db_session: Session) -> None:
    repo = SearchRepository(db_session)
    first = repo.search_dishes("Phở", PageRequest.of(2))
    second = repo.search_dishes("pho", PageRequest.of(2, first.next_cursor))
    assert first.has_next and second.has_next
    assert [item.item_id for item in first.items] == [1, 2]
    assert [item.item_id for item in second.items] == [3, 4]
    with pytest.raises(ValidationError):
        repo.search_dishes("quan", PageRequest.of(2, first.next_cursor))
    with pytest.raises(ValidationError):
        repo.search_restaurants("pho", PageRequest.of(2, first.next_cursor))
    with pytest.raises(ValidationError):
        repo.search_dishes("pho", PageRequest.of(2, ""))


def test_search_block_is_bidirectional_and_before_limit(db_session: Session) -> None:
    db_session.execute(text("INSERT INTO user_blocks(blocker_id,blocked_id) VALUES (1,2)"))
    db_session.execute(text("UPDATE posts SET user_id=2 WHERE id IN (1,2)"))
    repo = SearchRepository(db_session)
    assert repo.search_posts("", PageRequest.of(1), 1).items[0].item_id == 3
    assert repo.search_posts("", PageRequest.of(1), 2).items[0].item_id == 1
    assert repo.search_posts("", PageRequest.of(1), None).items[0].item_id == 1


def test_search_wildcards_are_literals_and_relevance_is_ordered(db_session: Session) -> None:
    db_session.execute(text("UPDATE dishes SET name='Phở', name_normalized='pho' WHERE id=2"))
    repo = SearchRepository(db_session)
    assert repo.search_dishes("Phở", PageRequest.of(2)).items[0].item_id == 2
    for pattern in ("%", "_", chr(92)):
        assert not repo.search_dishes(pattern, PageRequest.of()).items


def test_mixed_search_paginates_with_repository_edge_cursors(db_session: Session) -> None:
    db_session.execute(text("UPDATE dishes SET name='Đậu', name_normalized='dau' WHERE id=1"))
    db_session.execute(text("UPDATE restaurants SET name='Đậu', name_normalized='dau' WHERE id=1"))
    repo = SearchRepository(db_session)
    first = repo.search("Đậu", PageRequest.of(2), viewer_id=1)
    connection = PageMapper.to_connection(first, lambda hit: hit.kind)
    assert [edge.node for edge in connection.edges] == ["DISH", "RESTAURANT"]
    assert connection.page_info.has_next_page
    assert connection.page_info.end_cursor == first.next_cursor
    from_first_edge = repo.search("dau", PageRequest.of(1, connection.edges[0].cursor), viewer_id=1)
    assert [(hit.kind, hit.item_id) for hit in from_first_edge.items] == [("RESTAURANT", 1)]
    second = repo.search(
        normalize("NFD", "Đậu"), PageRequest.of(2, connection.page_info.end_cursor), viewer_id=1
    )
    assert [(hit.kind, hit.item_id) for hit in second.items] == [("POST", 1), ("POST", 101)]
    assert not second.has_next
    with pytest.raises(ValidationError):
        repo.search("dau", PageRequest.of(2, first.next_cursor), 1, type_filter="DISH")
    with pytest.raises(ValidationError):
        repo.search("dau", PageRequest.of(2, first.next_cursor), 2)


def test_search_accepts_injected_block_lookup(db_session: Session) -> None:
    class BlockFake:
        def list_blocked_user_ids(self, viewer_id: int) -> set[int]:
            assert viewer_id == 1
            return {2}

    db_session.execute(text("UPDATE posts SET user_id=2 WHERE id=1"))
    repo = SearchRepository(db_session, BlockFake())
    assert repo.search_posts("", PageRequest.of(1), 1).items[0].item_id == 2


def test_nearby_retains_dateline_and_polar_candidates(db_session: Session) -> None:
    db_session.execute(text("UPDATE restaurants SET latitude=0,longitude=-179.99 WHERE id=1"))
    repo = SearchRepository(db_session)
    assert [item.restaurant_id for item in repo.find_nearby(0, 179.99)] == [1]
    db_session.execute(text("UPDATE restaurants SET latitude=89.99,longitude=-50 WHERE id=1"))
    assert [item.restaurant_id for item in repo.find_nearby(89.99, 120)] == [1]


def test_nearby_reports_location_field_error_without_querying_db() -> None:
    with Session() as session, pytest.raises(ValidationError) as error:
        SearchRepository(session).find_nearby(91, 0)
    assert error.value.field_errors[0].code == "LOCATION_INVALID"
