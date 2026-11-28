"""Search validation and GraphQL results across the real PostgreSQL repository."""

import pytest
import strawberry
from app.core.clock import Clock
from app.core.container import RequestScope
from app.core.exceptions import ValidationError
from app.core.identity import UnavailableSessionVerifier
from app.core.pagination import Edge, PageRequest, RepositoryPage
from app.core.transaction import TransactionManager
from app.graphql.context import RequestContext
from app.graphql.search import SearchQuery
from app.repositories.search_details import SearchDetails, SearchDetailsRepository
from app.repositories.search_repo import SearchHit, SearchKind, SearchRepository
from app.services.discovery_search import DiscoverySearchService
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from tomateto.domain.content.normalization import normalize_name


@pytest.mark.parametrize("query", [" P ", "", "   "])
def test_short_query_is_validation_error_without_specific_label(query: str) -> None:
    with Session() as session, pytest.raises(ValidationError) as error:
        DiscoverySearchService(SearchRepository(session), SearchDetailsRepository(session)).search(
            query, PageRequest.of(), None
        )
    assert error.value.code == "VALIDATION_FAILED"
    assert error.value.field_errors[0].field == "query"
    assert error.value.field_errors[0].code == ""


def test_search_rejects_query_that_normalizes_to_empty() -> None:
    with Session() as session:
        repo = SearchRepository(session)
        service = DiscoverySearchService(repo, SearchDetailsRepository(session))
        for search in (
            lambda: repo.search("\u0301\u0301", PageRequest.of()),
            lambda: service.search("\u0301\u0301", PageRequest.of(), None),
        ):
            with pytest.raises(ValidationError) as error:
                search()
            assert error.value.code == "VALIDATION_FAILED"
            assert error.value.field_errors[0].field == "query"
            assert error.value.field_errors[0].code == ""


def test_search_uses_db_name_normalization_for_query_and_cursor(db_session: Session) -> None:
    # Use the same normalizer as DB's content writers, including đ and Unicode marks.
    db_session.execute(
        text("UPDATE dishes SET name=:name,name_normalized=:normalized WHERE id=:id"),
        [
            {"id": 1, "name": "Đà Lạt", "normalized": normalize_name("Đà Lạt")},
            {"id": 2, "name": "Đà Lạt 2", "normalized": normalize_name("Đà Lạt 2")},
        ],
    )
    repo = SearchRepository(db_session)
    first = repo.search("  ĐÀ    LẠT ", PageRequest.of(1), type_filter="DISH")
    assert [hit.item_id for hit in first.items] == [1]
    assert first.has_next and first.next_cursor is not None
    second = repo.search("da\tla\u0323t", PageRequest.of(1, first.next_cursor), type_filter="DISH")
    assert [hit.item_id for hit in second.items] == [2]
    assert not second.has_next


def test_search_refills_when_posts_become_invisible_during_detail_loading() -> None:
    """The next cursor is always usable even if an entire first page disappears."""

    class Reader:
        def __init__(self) -> None:
            self.cursors: list[str | None] = []

        def search(
            self,
            query: str,
            page: PageRequest,
            viewer_id: int | None = None,
            *,
            type_filter: SearchKind | None = None,
        ) -> RepositoryPage[SearchHit]:
            self.cursors.append(page.after)
            batches = {
                None: ([1, 2], True),
                "c2": ([3, 4], True),
                "c4": ([5], False),
            }
            ids, has_next = batches[page.after]
            return RepositoryPage(
                [Edge(f"c{id_}", SearchHit("POST", id_, "Phở", 1, 3)) for id_ in ids],
                has_next,
            )

    class Details:
        def load(self, result: RepositoryPage[SearchHit], viewer_id: int | None) -> SearchDetails:
            # Posts 1 and 2 were hidden or blocked after the initial query.
            visible = [{"id": hit.item_id} for hit in result.items if hit.item_id > 2]
            return SearchDetails([], visible, [], viewer_id)

    reader = Reader()
    result = DiscoverySearchService(reader, Details()).search("pho", PageRequest.of(2), 1)
    assert reader.cursors == [None, "c2", "c4"]
    assert [edge.node.item_id for edge in result.result.edges] == [3, 4]
    assert result.result.has_next
    assert result.result.next_cursor == "c4"


def test_search_refills_after_concurrent_hide_on_another_connection(
    session_factory: sessionmaker[Session],
) -> None:
    class HideDuringHydration(SearchDetailsRepository):
        def __init__(self, session: Session) -> None:
            super().__init__(session)
            self.changed = False

        def load(self, result: RepositoryPage[SearchHit], viewer_id: int | None) -> SearchDetails:
            if not self.changed:
                self.changed = True
                with session_factory.begin() as writer:
                    writer.execute(text("UPDATE posts SET is_hidden=true WHERE id IN (1,2)"))
            return super().load(result, viewer_id)

    try:
        with session_factory() as session:
            service = DiscoverySearchService(
                SearchRepository(session), HideDuringHydration(session)
            )
            page = service.search("pho", PageRequest.of(2), None, type_filter="POST")
            assert [edge.node.item_id for edge in page.result.edges] == [3, 4]
            assert page.result.has_next
            next_page = service.search(
                "pho", PageRequest.of(2, page.result.next_cursor), None, type_filter="POST"
            )
            assert [edge.node.item_id for edge in next_page.result.edges] == [5, 6]
    finally:
        with session_factory.begin() as writer:
            writer.execute(text("UPDATE posts SET is_hidden=false WHERE id IN (1,2)"))


def test_details_rechecks_block_when_lookup_result_is_stale(db_session: Session) -> None:
    class StaleBlockLookup:
        def list_blocked_user_ids(self, viewer_id: int) -> set[int]:
            return set()

    db_session.execute(text("UPDATE posts SET user_id=2 WHERE id IN (1,2)"))
    db_session.execute(text("INSERT INTO user_blocks(blocker_id,blocked_id) VALUES (1,2)"))
    lookup = StaleBlockLookup()
    result = DiscoverySearchService(
        SearchRepository(db_session, lookup), SearchDetailsRepository(db_session, lookup)
    ).search("pho", PageRequest.of(2), 1, type_filter="POST")
    assert [edge.node.item_id for edge in result.result.edges] == [3, 4]
    assert result.result.has_next
    assert result.result.next_cursor is not None


def test_search_graphql_on_real_database(db_session: Session) -> None:
    db_session.execute(
        text("UPDATE restaurants SET name='Phở quán',name_normalized='pho quan' WHERE id=1")
    )
    schema = strawberry.Schema(query=SearchQuery)
    scope = RequestScope(db_session, TransactionManager(db_session), UnavailableSessionVerifier())
    context = RequestContext(None, scope, Clock())
    query = """
      query($q:String!, $page:PageInput) {
        search(query:$q,page:$page) {
          edges { cursor node { type dish { id name } restaurant { id name }
                                post { id dishName caption author { id displayName }
                                       images { id url position } likeCount } } }
          pageInfo { endCursor hasNextPage }
        }
      }
    """
    first = schema.execute_sync(
        query, variable_values={"q": "phở", "page": {"first": 50}}, context_value=context
    )
    assert not first.errors
    assert first.data is not None
    result = first.data["search"]
    assert result["pageInfo"]["hasNextPage"]
    assert result["edges"][0]["node"]["dish"]["name"].startswith("Phở")
    end = result["pageInfo"]["endCursor"]
    second = schema.execute_sync(
        query,
        variable_values={"q": "pho", "page": {"first": 50, "after": end}},
        context_value=context,
    )
    assert not second.errors and second.data is not None
    assert not {edge["cursor"] for edge in result["edges"]}.intersection(
        edge["cursor"] for edge in second.data["search"]["edges"]
    )
    empty = schema.execute_sync(query, variable_values={"q": "zzzzzz"}, context_value=context)
    assert not empty.errors and empty.data is not None
    assert empty.data["search"]["edges"] == []
    assert not empty.data["search"]["pageInfo"]["hasNextPage"]
    invalid = schema.execute_sync(
        query, variable_values={"q": "pho", "page": {"after": "bad"}}, context_value=context
    )
    assert invalid.errors
    assert isinstance(invalid.errors[0].original_error, ValidationError)
    assert invalid.errors[0].original_error.field_errors[0].code == "CURSOR_INVALID"
