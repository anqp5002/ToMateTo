"""Caller-transaction snapshot publication and viewer-filtered dish reads."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.core.pagination import CursorCodec, PageRequest, TrendingCursor
from app.models.trending import (
    TrendingDishSnapshot,
    TrendingPostSnapshot,
    TrendingRun,
    TrendingTagSnapshot,
)
from app.repositories.block_lookup import BlockLookup, PostgresBlockLookup
from app.repositories.page import RepositoryPage


@dataclass(frozen=True)
class SnapshotScore:
    target_id: int
    score: Decimal


@dataclass(frozen=True)
class TrendingDish:
    dish_id: int
    name: str
    score: Decimal


class TrendingSnapshotRepository:
    def __init__(self, session: Session, block_lookup: BlockLookup | None = None) -> None:
        self._session = session
        self._codec = CursorCodec()
        self._blocks = block_lookup if block_lookup is not None else PostgresBlockLookup(session)

    def latest_run(self) -> TrendingRun | None:
        return self._session.scalar(
            select(TrendingRun)
            .order_by(
                TrendingRun.published_at.desc(),
                TrendingRun.id.desc(),
            )
            .limit(1)
        )

    def find_run(self, run_id: int) -> TrendingRun | None:
        return self._session.get(TrendingRun, run_id)

    def publish(
        self,
        run: TrendingRun,
        posts: list[SnapshotScore],
        dishes: list[SnapshotScore],
        tags: list[SnapshotScore] | None = None,
    ) -> TrendingRun:
        """Flush all groups together; the owning service commits or rolls back."""
        self._session.add(run)
        self._session.flush()
        self._session.add_all(
            [TrendingPostSnapshot(run_id=run.id, post_id=s.target_id, score=s.score) for s in posts]
        )
        self._session.add_all(
            [
                TrendingDishSnapshot(run_id=run.id, dish_id=s.target_id, score=s.score)
                for s in dishes
            ]
        )
        self._session.add_all(
            [
                TrendingTagSnapshot(run_id=run.id, tag_id=s.target_id, score=s.score)
                for s in tags or []
            ]
        )
        self._session.flush()
        return run

    def list_dishes(
        self, run_id: int, page: PageRequest, viewer_id: int | None = None
    ) -> RepositoryPage[TrendingDish]:
        scope = f"trending-dishes:{viewer_id}"
        key: TrendingCursor | None = None
        if page.after is not None:
            decoded = self._codec.decode(page.after, "TRENDING", run_id=run_id, scope=scope)
            if not isinstance(decoded, TrendingCursor):
                raise ValidationError()
            key = decoded
        statement = text("""
            SELECT s.dish_id, d.name, s.score
            FROM trending_dish_snapshots s JOIN dishes d ON d.id=s.dish_id
            WHERE s.run_id=:run_id AND EXISTS (
                SELECT 1 FROM trending_post_snapshots ps JOIN posts p ON p.id=ps.post_id
                WHERE ps.run_id=s.run_id AND p.dish_id=s.dish_id AND NOT p.is_hidden
                AND p.user_id <> ALL(CAST(:blocked_user_ids AS bigint[]))
            ) AND (CAST(:after_score AS numeric) IS NULL
                   OR (s.score,s.dish_id)<(:after_score,:after_id))
            ORDER BY s.score DESC,s.dish_id DESC LIMIT :limit
        """)
        rows = (
            self._session.execute(
                statement,
                {
                    "run_id": run_id,
                    "blocked_user_ids": list(self._blocks.list_blocked_user_ids(viewer_id))
                    if viewer_id is not None
                    else [],
                    "after_score": key.score if key else None,
                    "after_id": key.target_id if key else None,
                    "limit": page.first + 1,
                },
            )
            .mappings()
            .all()
        )
        items = [TrendingDish(int(r["dish_id"]), str(r["name"]), Decimal(r["score"])) for r in rows]
        return RepositoryPage.from_rows(
            items,
            page,
            lambda item: self._codec.encode_trending(run_id, item.score, item.dish_id, scope=scope),
        )
