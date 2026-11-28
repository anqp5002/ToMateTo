"""Caller-transaction snapshot publication and viewer-filtered dish reads."""

from dataclasses import dataclass
from datetime import datetime
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

SCORE_SQL = """
WITH bounds AS (
    SELECT CAST(:end_at AS timestamptz) - interval '7 days' AS lo,
           CAST(:end_at AS timestamptz) AS hi
), eligible AS MATERIALIZED (
    SELECT p.id, p.dish_id, p.created_at FROM posts p CROSS JOIN bounds w
    WHERE NOT p.is_hidden AND p.created_at < w.hi
), likes_count AS (
    SELECT l.post_id, count(*)::numeric AS n
    FROM likes l JOIN eligible e ON e.id=l.post_id CROSS JOIN bounds w
    WHERE l.created_at >= w.lo AND l.created_at < w.hi GROUP BY l.post_id
), saves AS (
    SELECT ci.post_id, c.user_id, min(ci.added_at) AS first_save
    FROM collection_items ci JOIN collections c ON c.id=ci.collection_id
    JOIN eligible e ON e.id=ci.post_id GROUP BY ci.post_id,c.user_id
), save_count AS (
    SELECT s.post_id, count(*)::numeric AS n FROM saves s CROSS JOIN bounds w
    WHERE s.first_save >= w.lo AND s.first_save < w.hi GROUP BY s.post_id
), scored AS (
    SELECT e.id AS post_id,e.dish_id,
           CASE WHEN e.created_at >= w.lo THEN 1 ELSE 0 END AS new_post,
           coalesce(l.n,0)+coalesce(s.n,0) AS post_score,
           CASE WHEN e.created_at >= w.lo THEN 1 ELSE 0 END
               + coalesce(l.n,0)+coalesce(s.n,0) AS dish_score
    FROM eligible e CROSS JOIN bounds w LEFT JOIN likes_count l ON l.post_id=e.id
    LEFT JOIN save_count s ON s.post_id=e.id
)
SELECT s.post_id,s.dish_id,s.new_post,s.post_score,s.dish_score,
       coalesce(array_agg(pt.tag_id ORDER BY pt.tag_id)
           FILTER (WHERE pt.tag_id IS NOT NULL), ARRAY[]::bigint[]) AS tag_ids
FROM scored s LEFT JOIN post_tags pt ON pt.post_id=s.post_id
WHERE s.dish_score > 0
GROUP BY s.post_id,s.dish_id,s.new_post,s.post_score,s.dish_score ORDER BY s.post_id
"""


@dataclass(frozen=True)
class ScoredPost:
    post_id: int
    dish_id: int
    post_score: Decimal
    dish_score: Decimal
    tag_ids: tuple[int, ...]


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

    def compute_scores(self, end_at: datetime) -> list[ScoredPost]:
        """Read all inputs in one database snapshot for the seven-day scores."""
        rows = self._session.execute(text(SCORE_SQL), {"end_at": end_at}).mappings()
        return [
            ScoredPost(
                int(row["post_id"]),
                int(row["dish_id"]),
                Decimal(row["post_score"]),
                Decimal(row["dish_score"]),
                tuple(row["tag_ids"]),
            )
            for row in rows
        ]

    def try_lock_for_publish(self) -> bool:
        return bool(self._session.scalar(text("SELECT pg_try_advisory_xact_lock(7101, 1)")))

    def latest_window_end(self) -> datetime | None:
        return self._session.scalar(
            select(TrendingRun.window_end)
            .order_by(TrendingRun.window_end.desc(), TrendingRun.id.desc())
            .limit(1)
        )

    def lock_publication_targets(self, scores: list[ScoredPost], tags: list[int]) -> bool:
        """Lock staged parents in stable order and confirm none changed or disappeared."""
        posts = [item.post_id for item in scores]
        dishes = sorted({item.dish_id for item in scores})
        locked = self._session.execute(
            text("SELECT id,dish_id,is_hidden FROM posts WHERE id=ANY(:ids) ORDER BY id FOR SHARE"),
            {"ids": posts},
        ).all()
        if [(r.id, r.dish_id, r.is_hidden) for r in locked] != [
            (item.post_id, item.dish_id, False) for item in scores
        ]:
            return False
        for statement, ids in (
            ("SELECT id FROM dishes WHERE id=ANY(:ids) ORDER BY id FOR KEY SHARE", dishes),
            ("SELECT id FROM tags WHERE id=ANY(:ids) ORDER BY id FOR KEY SHARE", tags),
        ):
            if not ids:
                continue
            found = self._session.scalars(text(statement), {"ids": ids}).all()
            if list(found) != ids:
                return False
        return True

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
