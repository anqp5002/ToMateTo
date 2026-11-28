"""S9 trending score, snapshot pagination, and rollback on PostgreSQL."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.core.clock import Clock
from app.core.exceptions import ValidationError
from app.core.pagination import PageRequest
from app.jobs.runner import JobSkippedError
from app.models.trending import TrendingRun
from app.repositories.trending_repo import ScoredPost, SnapshotScore, TrendingSnapshotRepository
from app.services.trending_service import TrendingService
from sqlalchemy import text
from sqlalchemy.orm import Session


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 11, 22, tzinfo=UTC)


def test_service_uses_repository_and_keeps_unapproved_tags_disabled() -> None:
    service = TrendingService(MagicMock(spec=Session), FixedClock())
    repo = MagicMock(spec=TrendingSnapshotRepository)
    service.repo = repo
    score = ScoredPost(1, 2, Decimal(3), Decimal(4), (9,))
    repo.compute_scores.return_value = [score]
    repo.try_lock_for_publish.return_value = True
    repo.latest_window_end.return_value = None
    repo.lock_publication_targets.return_value = True

    rows = service.compute(FixedClock().now())
    assert service._publish(FixedClock().now(), rows) == 2
    repo.lock_publication_targets.assert_called_once_with([score], [])
    _, posts, dishes, tags = repo.publish.call_args.args
    assert posts == [SnapshotScore(1, Decimal(3))]
    assert dishes == [SnapshotScore(2, Decimal(4))]
    assert tags == []


def test_changed_publication_targets_skip_without_publishing() -> None:
    service = TrendingService(MagicMock(spec=Session), FixedClock())
    repo = MagicMock(spec=TrendingSnapshotRepository)
    service.repo = repo
    repo.try_lock_for_publish.return_value = True
    repo.latest_window_end.return_value = None
    repo.lock_publication_targets.return_value = False

    with pytest.raises(JobSkippedError):
        service._publish(FixedClock().now(), [ScoredPost(1, 2, Decimal(3), Decimal(4), ())])
    repo.publish.assert_not_called()


def test_score_deduplicates_saves_and_excludes_hidden(db_session: Session) -> None:
    now = FixedClock().now()
    db_session.execute(text("UPDATE posts SET created_at=:t"), {"t": now - timedelta(days=10)})
    db_session.execute(
        text("UPDATE posts SET created_at=:t WHERE id IN (1,2,3)"), {"t": now - timedelta(days=1)}
    )
    db_session.execute(text("UPDATE posts SET is_hidden=true WHERE id=3"))
    db_session.execute(
        text("INSERT INTO likes(user_id,post_id,created_at) VALUES (2,1,:t),(3,1,:t)"),
        {"t": now - timedelta(days=2)},
    )
    db_session.execute(
        text(
            "INSERT INTO collections(id,user_id,name,name_normalized) VALUES "
            "(111,2,'one','one'),(112,2,'two','two')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO collection_items(collection_id,post_id,added_at) VALUES "
            "(111,1,:t),(112,1,:t)"
        ),
        {"t": now - timedelta(days=1)},
    )
    rows = TrendingService(db_session, FixedClock()).compute(now)
    assert [(r.post_id, r.post_score, r.dish_score) for r in rows] == [
        (1, Decimal(3), Decimal(4)),
        (2, Decimal(0), Decimal(1)),
    ]


def test_tag_snapshot_counts_new_posts_and_their_interactions(db_session: Session) -> None:
    """A tag uses new-post count plus post scores, excluding hidden posts."""
    now = FixedClock().now()
    db_session.execute(text("UPDATE posts SET created_at=:t"), {"t": now - timedelta(days=10)})
    db_session.execute(
        text("UPDATE posts SET created_at=:t WHERE id IN (1,3,4)"),
        {"t": now - timedelta(days=1)},
    )
    db_session.execute(text("UPDATE posts SET is_hidden=true WHERE id=3"))
    db_session.execute(
        text("INSERT INTO likes(user_id,post_id,created_at) VALUES (2,1,:t),(3,2,:t)"),
        {"t": now - timedelta(days=2)},
    )
    db_session.execute(
        text(
            "INSERT INTO tags(id,name,name_normalized) VALUES "
            "(1,'Tag 1','tag 1'),(2,'Tag 2','tag 2')"
        )
    )
    db_session.execute(text("INSERT INTO post_tags(post_id,tag_id) VALUES (1,1),(2,1),(3,1),(4,2)"))

    service = TrendingService(db_session, FixedClock())
    scores = service.compute(now)
    service._publish(now, scores)
    assert db_session.scalar(text("SELECT count(*) FROM trending_tag_snapshots")) == 0
    assert db_session.scalar(text("SELECT count(*) FROM trending_post_snapshots")) > 0
    assert db_session.scalar(text("SELECT count(*) FROM trending_dish_snapshots")) > 0

    # Q15 proposal stays off until explicitly enabled after approval.
    service_enabled = TrendingService(db_session, FixedClock(), tags_enabled=True)
    service_enabled._publish(now + timedelta(microseconds=1), scores)
    tags = db_session.execute(
        text("SELECT tag_id,score FROM trending_tag_snapshots ORDER BY tag_id")
    ).all()
    # Tag 1: one new post + two likes; old post 2 contributes its like only.
    # Hidden post 3 contributes nothing. Tag 2 has one new post and no likes.
    assert [(row.tag_id, row.score) for row in tags] == [(1, Decimal(3)), (2, Decimal(1))]


def test_waiting_and_cursor_continues_original_run(db_session: Session) -> None:
    service = TrendingService(db_session, FixedClock())
    assert service.get_trending(PageRequest.of(), None).state == "WAITING"
    now = FixedClock().now()
    first = service.repo.publish(
        TrendingRun(window_start=now - timedelta(days=7), window_end=now, formula_version="v1"),
        [SnapshotScore(1, Decimal(2)), SnapshotScore(2, Decimal(1))],
        [SnapshotScore(1, Decimal(2)), SnapshotScore(2, Decimal(1))],
    )
    page1 = service.get_trending(PageRequest.of(1), None)
    assert page1.state == "READY" and page1.connection.page_info.has_next_page
    service.repo.publish(
        TrendingRun(window_start=now, window_end=now + timedelta(days=7), formula_version="v1"),
        [SnapshotScore(1, Decimal(9))],
        [SnapshotScore(1, Decimal(9))],
    )
    page2 = service.get_trending(PageRequest.of(1, page1.connection.page_info.end_cursor), None)
    assert page2.connection.edges[0].node.dish_id == 2
    db_session.delete(first)
    db_session.flush()
    with pytest.raises(ValidationError):
        service.get_trending(PageRequest.of(1, page1.connection.page_info.end_cursor), None)


def test_failed_publication_preserves_previous_run(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = TrendingService(db_session, FixedClock())
    now = FixedClock().now()
    old = service.repo.publish(
        TrendingRun(
            window_start=now - timedelta(days=14),
            window_end=now - timedelta(days=7),
            formula_version="old",
        ),
        [],
        [],
    )
    db_session.flush()
    old_id = old.id

    def fail(*args: object, **kwargs: object) -> None:
        db_session.add(
            TrendingRun(
                window_start=now - timedelta(days=7), window_end=now, formula_version="incomplete"
            )
        )
        db_session.flush()
        raise RuntimeError("simulated tag write failure")

    monkeypatch.setattr(service.repo, "publish", fail)
    # Rollback of the nested savepoint must preserve the previous published run.
    with pytest.raises(RuntimeError), db_session.begin_nested():
        service._publish(now, [])
    assert service.repo.latest_run().id == old_id  # type: ignore[union-attr]
