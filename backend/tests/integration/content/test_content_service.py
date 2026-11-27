"""Service-level S9 tests for feed single-pass projection, validation bounds, and contracts."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session
from tomateto.business.content.contracts import ContentWritePolicy, PostInput, RecipeInput
from tomateto.business.content.feed_service import FeedQueryService
from tomateto.business.content.post_service import PostLifecycleService
from tomateto.dataaccess.content.post_repo import PostRepository
from tomateto.domain.content.paging import PageRequest as RepositoryPageRequest
from tomateto.shared.exceptions import ValidationError
from tomateto.shared.identity import Principal
from tomateto.shared.pagination import PageRequest


class FrozenClock:
    def now(self) -> datetime:
        return datetime(2030, 1, 1, tzinfo=UTC)


def test_latest_feed_skips_redundant_post_repo_hydration(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_repo_feed(
        self: PostRepository,
        mode: str,
        page: RepositoryPageRequest,
        viewer_id: int | None = None,
        blocked_user_ids: list[int] | None = None,
    ) -> object:
        raise AssertionError("PostRepository.list_feed must not be called")

    def fail_repo_author(
        self: PostRepository,
        author_id: int,
        page: RepositoryPageRequest,
        viewer_id: int | None = None,
    ) -> object:
        raise AssertionError("PostRepository.list_by_author must not be called")

    monkeypatch.setattr(PostRepository, "list_feed", fail_repo_feed)
    monkeypatch.setattr(PostRepository, "list_by_author", fail_repo_author)

    service = PostLifecycleService(session, ContentWritePolicy(), FrozenClock())
    created = service.create_post(Principal(1, "jti-1", 0), PostInput(dish_name="Cơm tấm"))
    feed_service = FeedQueryService(session)

    global_page = feed_service.latest(PageRequest.of(10), None)
    assert any(edge.node.id == created.id for edge in global_page.edges)

    author_page = feed_service.latest(PageRequest.of(10), None, author_id=1)
    assert any(edge.node.id == created.id for edge in author_page.edges)


def test_recipe_input_forbids_extra_fields() -> None:
    with pytest.raises(PydanticValidationError):
        RecipeInput.model_validate({"ingredients": ["Phở"], "unknown": 1})


@pytest.mark.parametrize("bad_id", [0, -1, 9_223_372_036_854_775_808])
def test_bigint_bounds_rejected_on_get_post_and_create_post(session: Session, bad_id: int) -> None:
    feed_service = FeedQueryService(session)
    with pytest.raises(ValidationError) as exc_get:
        feed_service.get_post(bad_id, None)
    assert exc_get.value.field_errors[0].field == "id"

    post_service = PostLifecycleService(session, ContentWritePolicy(), FrozenClock())
    with pytest.raises(ValidationError) as exc_create:
        post_service.create_post(
            Principal(1, "jti-1", 0), PostInput(dish_name="Phở", restaurant_id=bad_id)
        )
    assert exc_create.value.field_errors[0].field == "restaurantId"
