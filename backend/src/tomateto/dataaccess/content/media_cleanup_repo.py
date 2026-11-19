import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tomateto.dataaccess.content.common import snapshot
from tomateto.dataaccess.schema import media_assets, media_cleanup_jobs
from tomateto.domain.content.records import MediaCleanupJobRecord


class MediaCleanupRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(self, asset_ids: list[UUID]) -> list[MediaCleanupJobRecord]:
        if not asset_ids:
            return []
        ids = sorted(set(asset_ids))
        assets = list(
            self.session.execute(
                select(media_assets)
                .where(media_assets.c.id.in_(ids))
                .order_by(media_assets.c.id)
                .with_for_update()
            ).mappings()
        )
        if len(assets) != len(ids) or any(a["state"] != "DELETE_PENDING" for a in assets):
            raise ValueError("Enqueue requires existing DELETE_PENDING assets")
        self.session.execute(
            insert(media_cleanup_jobs)
            .values([{"media_id": asset_id} for asset_id in ids])
            .on_conflict_do_nothing(constraint="uq_media_cleanup_jobs_media_id")
        )
        rows = self.session.execute(
            select(media_cleanup_jobs)
            .where(media_cleanup_jobs.c.media_id.in_(ids))
            .order_by(media_cleanup_jobs.c.id)
        ).mappings()
        return [snapshot(MediaCleanupJobRecord, row) for row in rows]

    def list_due(self, now: datetime, limit: int = 50) -> list[MediaCleanupJobRecord]:
        if limit < 1:
            raise ValueError("limit must be positive")
        # Read only: not a durable multi-worker claim. V1 has one cleanup worker.
        rows = self.session.execute(
            select(media_cleanup_jobs)
            .where(
                media_cleanup_jobs.c.completed_at.is_(None),
                media_cleanup_jobs.c.next_attempt_at <= now,
            )
            .order_by(media_cleanup_jobs.c.next_attempt_at, media_cleanup_jobs.c.id)
            .limit(limit)
        ).mappings()
        return [snapshot(MediaCleanupJobRecord, row) for row in rows]

    def mark_completed(self, job_id: int, now: datetime) -> None:
        self.session.execute(
            update(media_cleanup_jobs)
            .where(media_cleanup_jobs.c.id == job_id, media_cleanup_jobs.c.completed_at.is_(None))
            .values(completed_at=now, last_error_code=None)
        )

    def record_failure(self, job_id: int, next_attempt_at: datetime, error_code: str) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", error_code):
            raise ValueError("Store a sanitized error code, never a raw provider exception")
        self.session.execute(
            update(media_cleanup_jobs)
            .where(media_cleanup_jobs.c.id == job_id, media_cleanup_jobs.c.completed_at.is_(None))
            .values(
                attempts=media_cleanup_jobs.c.attempts + 1,
                next_attempt_at=next_attempt_at,
                last_error_code=error_code,
            )
        )
