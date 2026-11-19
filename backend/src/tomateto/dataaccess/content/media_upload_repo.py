from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from tomateto.dataaccess.content.common import snapshot, values
from tomateto.dataaccess.schema import media_assets
from tomateto.domain.content.records import MediaAssetRecord


class UploadRejectedError(ValueError):
    """Internal rejection reason; public DomainError mapping belongs to BE service."""


class MediaUploadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, upload: MediaAssetRecord) -> MediaAssetRecord:
        row = (
            self.session.execute(
                insert(media_assets).values(**values(upload)).returning(media_assets)
            )
            .mappings()
            .one()
        )
        return snapshot(MediaAssetRecord, row)

    def find_by_id(self, upload_id: UUID) -> MediaAssetRecord | None:
        row = (
            self.session.execute(select(media_assets).where(media_assets.c.id == upload_id))
            .mappings()
            .first()
        )
        return snapshot(MediaAssetRecord, row) if row else None

    def consume(
        self, upload_id: UUID, owner_id: int, purpose: str, now: datetime
    ) -> MediaAssetRecord:
        if now.tzinfo is None:
            raise ValueError("Use an aware timestamp")
        row = (
            self.session.execute(
                select(media_assets).where(media_assets.c.id == upload_id).with_for_update()
            )
            .mappings()
            .first()
        )
        if not row:
            raise UploadRejectedError("MISSING")
        if row["owner_id"] != owner_id:
            raise UploadRejectedError("OWNER")
        if row["purpose"] != purpose:
            raise UploadRejectedError("PURPOSE")
        if row["state"] != "PENDING":
            raise UploadRejectedError("STATE")
        if row["expires_at"] <= now:
            raise UploadRejectedError("EXPIRED")
        updated = (
            self.session.execute(
                update(media_assets)
                .where(media_assets.c.id == upload_id)
                .values(state="ATTACHED", consumed_at=now)
                .returning(media_assets)
            )
            .mappings()
            .one()
        )
        return snapshot(MediaAssetRecord, updated)

    def mark_deleted(self, asset_id: UUID, now: datetime) -> None:
        if now.tzinfo is None:
            raise ValueError("Use an aware timestamp")
        row = self.session.execute(
            update(media_assets)
            .where(media_assets.c.id == asset_id, media_assets.c.state == "DELETE_PENDING")
            .values(state="DELETED", deleted_at=now)
            .returning(media_assets.c.id)
        ).first()
        if not row:
            raise UploadRejectedError("STATE")

    def list_expired(self, now: datetime) -> list[MediaAssetRecord]:
        rows = self.session.execute(
            select(media_assets)
            .where(media_assets.c.state == "PENDING", media_assets.c.expires_at <= now)
            .order_by(media_assets.c.id)
        ).mappings()
        return [snapshot(MediaAssetRecord, row) for row in rows]
