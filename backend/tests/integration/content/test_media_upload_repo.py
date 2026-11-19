from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from tomateto.dataaccess.content.media_cleanup_repo import MediaCleanupRepository
from tomateto.dataaccess.content.media_upload_repo import MediaUploadRepository, UploadRejectedError
from tomateto.dataaccess.schema import media_assets, media_cleanup_jobs

from db.testing import asset_record

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def test_consume_transitions_and_reuse_is_rejected(session: Session) -> None:
    repo = MediaUploadRepository(session)
    asset = repo.create(asset_record())
    attached = repo.consume(asset.id, 1, "POST", NOW)
    assert attached.state == "ATTACHED" and attached.consumed_at == NOW
    with pytest.raises(UploadRejectedError, match="STATE"):
        repo.consume(asset.id, 1, "POST", NOW)


@pytest.mark.parametrize(
    "owner,purpose,at,reason",
    [
        (2, "POST", NOW, "OWNER"),
        (1, "COVER", NOW, "PURPOSE"),
        (1, "POST", NOW + timedelta(hours=1), "EXPIRED"),
    ],
)
def test_consume_invalid_ticket_leaves_pending(
    session: Session, owner: int, purpose: str, at: datetime, reason: str
) -> None:
    repo = MediaUploadRepository(session)
    asset = repo.create(asset_record())
    with pytest.raises(UploadRejectedError, match=reason):
        repo.consume(asset.id, owner, purpose, at)
    stored = repo.find_by_id(asset.id)
    assert stored is not None and stored.state == "PENDING"


def test_cleanup_enqueue_idempotent_completion_and_failure(session: Session) -> None:
    upload = MediaUploadRepository(session)
    asset = upload.create(asset_record(state="DELETE_PENDING"))
    cleanup = MediaCleanupRepository(session)
    job = cleanup.enqueue([asset.id])[0]
    assert cleanup.enqueue([asset.id])[0].id == job.id
    cleanup.record_failure(job.id, NOW, "PROVIDER_TIMEOUT")
    due = cleanup.list_due(NOW)
    assert len(due) == 1 and due[0].attempts == 1 and due[0].last_error_code == "PROVIDER_TIMEOUT"
    upload.mark_deleted(asset.id, NOW)
    cleanup.mark_completed(job.id, NOW)
    assert cleanup.list_due(NOW) == []
    stored = upload.find_by_id(asset.id)
    assert stored is not None and stored.state == "DELETED"


def test_cleanup_rejects_attached_asset(session: Session) -> None:
    asset = MediaUploadRepository(session).create(asset_record(state="ATTACHED", consumed_at=NOW))
    with pytest.raises(ValueError, match="DELETE_PENDING"):
        MediaCleanupRepository(session).enqueue([asset.id])


def test_enqueue_rollback_restores_asset_state(session: Session) -> None:
    repo = MediaUploadRepository(session)
    asset = repo.create(asset_record())
    with pytest.raises(RuntimeError), session.begin_nested():
        session.execute(
            update(media_assets).where(media_assets.c.id == asset.id).values(state="DELETE_PENDING")
        )
        MediaCleanupRepository(session).enqueue([asset.id])
        raise RuntimeError("forced transaction failure")
    stored = repo.find_by_id(asset.id)
    assert stored is not None and stored.state == "PENDING"
    assert session.execute(select(media_cleanup_jobs)).first() is None
