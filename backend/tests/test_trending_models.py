"""Snapshot schema and cascading deletion."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.models.trending import TrendingDishSnapshot, TrendingRun
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_snapshot_key_and_run_cascade(db_session: Session) -> None:
    end = datetime(2026, 11, 18, tzinfo=UTC)
    run = TrendingRun(
        window_start=end - timedelta(days=7), window_end=end, formula_version="test-v1"
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(TrendingDishSnapshot(run_id=run.id, dish_id=1, score=Decimal("1.0000001")))
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(TrendingDishSnapshot(run_id=run.id, dish_id=1, score=Decimal("2")))
        db_session.flush()
    db_session.execute(delete(TrendingRun).where(TrendingRun.id == run.id))
    assert (
        db_session.scalar(select(TrendingDishSnapshot).where(TrendingDishSnapshot.run_id == run.id))
        is None
    )


def test_reversed_window_is_rejected(db_session: Session) -> None:
    end = datetime(2026, 11, 18, tzinfo=UTC)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(TrendingRun(window_start=end, window_end=end, formula_version="bad"))
        db_session.flush()
