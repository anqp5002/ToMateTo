from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.pagination import PageRequest
from app.models.trending import TrendingRun
from app.repositories.trending_repo import SnapshotScore, TrendingSnapshotRepository
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_publish_keeps_exact_scores_and_run(db_session: Session) -> None:
    repo = TrendingSnapshotRepository(db_session)
    assert repo.latest_run() is None
    end = datetime(2026, 11, 18, tzinfo=UTC)
    run = repo.publish(
        TrendingRun(
            window_start=end - timedelta(days=7), window_end=end, formula_version="test-v1"
        ),
        [SnapshotScore(1, Decimal("2"))],
        [SnapshotScore(1, Decimal("3.0000001"))],
    )
    latest = repo.latest_run()
    assert latest is not None and latest.id == run.id
    rows = repo.list_dishes(run.id, PageRequest.of(), viewer_id=None)
    assert rows.items[0].score == Decimal("3.0000001")


def test_dish_visibility_filter_runs_before_limit(db_session: Session) -> None:
    repo = TrendingSnapshotRepository(db_session)
    end = datetime(2026, 11, 18, tzinfo=UTC)
    run = repo.publish(
        TrendingRun(window_start=end - timedelta(days=7), window_end=end, formula_version="test"),
        [SnapshotScore(1, Decimal(10)), SnapshotScore(2, Decimal(5))],
        [SnapshotScore(1, Decimal(10)), SnapshotScore(2, Decimal(5))],
    )
    db_session.execute(text("UPDATE posts SET user_id=2 WHERE id=1"))
    db_session.execute(text("INSERT INTO user_blocks(blocker_id,blocked_id) VALUES (1,2)"))
    assert repo.list_dishes(run.id, PageRequest.of(1), 1).items[0].dish_id == 2
    assert repo.list_dishes(run.id, PageRequest.of(1), None).items[0].dish_id == 1
