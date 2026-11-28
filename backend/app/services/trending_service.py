"""Compute and read a published seven-day trending snapshot."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.exceptions import FieldError, ValidationError
from app.core.pagination import Connection, CursorCodec, PageMapper, PageRequest, TrendingCursor
from app.core.transaction import TransactionManager
from app.jobs.runner import JobSkippedError
from app.models.trending import TrendingRun
from app.repositories.trending_repo import (
    ScoredPost,
    SnapshotScore,
    TrendingDish,
    TrendingSnapshotRepository,
)


@dataclass(frozen=True)
class TrendingResult:
    state: str
    connection: Connection[TrendingDish]


class TrendingService:
    def __init__(
        self, session: Session, clock: Clock | None = None, *, tags_enabled: bool = False
    ) -> None:
        self.session = session
        self.clock = clock or Clock()
        self.tags_enabled = tags_enabled
        self.repo = TrendingSnapshotRepository(session)
        self.codec = CursorCodec()

    def get_trending(self, page: PageRequest, viewer_id: int | None) -> TrendingResult:
        if page.after is None:
            run = self.repo.latest_run()
        else:
            key = self.codec.decode(page.after, "TRENDING", scope=f"trending-dishes:{viewer_id}")
            if not isinstance(key, TrendingCursor):
                raise self._invalid_cursor()
            run = self.repo.find_run(key.run_id)
            if run is None:
                raise self._invalid_cursor()
        if run is None:
            from app.core.pagination import RepositoryPage

            empty: RepositoryPage[TrendingDish] = RepositoryPage([], False)
            return TrendingResult("WAITING", PageMapper.to_connection(empty, lambda item: item))
        found = self.repo.list_dishes(run.id, page, viewer_id)
        return TrendingResult("READY", PageMapper.to_connection(found, lambda item: item))

    @staticmethod
    def _invalid_cursor() -> ValidationError:
        msg = "Không thể tải trang tiếp. Vui lòng tải lại."
        return ValidationError(field_errors=[FieldError("page.after", "CURSOR_INVALID", msg)])

    def compute(self, end_at: datetime) -> list[ScoredPost]:
        return self.repo.compute_scores(end_at)

    def refresh(self) -> int:
        """Publish atomically; tag snapshots are a pending Q15 proposal and disabled by default."""
        end_at = self.clock.now()
        try:
            scores = self.compute(end_at)
        finally:
            self.session.rollback()
        return TransactionManager(self.session).run(lambda: self._publish(end_at, scores))

    def _publish(self, end_at: datetime, scores: list[ScoredPost]) -> int:
        if not self.repo.try_lock_for_publish():
            raise JobSkippedError()
        newest = self.repo.latest_window_end()
        if newest is not None and newest >= end_at:
            raise JobSkippedError()
        tags = sorted({tag for item in scores for tag in item.tag_ids}) if self.tags_enabled else []
        if not self.repo.lock_publication_targets(scores, tags):
            raise JobSkippedError()
        dish_scores: dict[int, Decimal] = defaultdict(Decimal)
        tag_scores: dict[int, Decimal] = defaultdict(Decimal)
        for item in scores:
            dish_scores[item.dish_id] += item.dish_score
            if self.tags_enabled:
                for tag in item.tag_ids:
                    tag_scores[tag] += item.dish_score
        self.repo.publish(
            TrendingRun(
                window_start=end_at - timedelta(days=7), window_end=end_at, formula_version="v1-7d"
            ),
            [SnapshotScore(item.post_id, item.post_score) for item in scores],
            [SnapshotScore(key, value) for key, value in sorted(dish_scores.items())],
            [SnapshotScore(key, value) for key, value in sorted(tag_scores.items())],
        )
        return len(scores) + len(dish_scores) + len(tag_scores)
