"""Upload I/O precedes the short transaction which registers a PENDING asset."""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from tomateto.business.content.contracts import MediaStorage, TimeSource, WritePolicy, invalid
from tomateto.dataaccess.content.media_upload_repo import MediaUploadRepository
from tomateto.domain.content.records import MediaAssetRecord
from tomateto.integration.media_storage import process_image
from tomateto.shared.exceptions import IntegrationError
from tomateto.shared.identity import Principal
from tomateto.shared.transaction import TransactionManager


class MediaService:
    def __init__(
        self, session: Session, storage: MediaStorage, policy: WritePolicy, clock: TimeSource
    ) -> None:
        self.session, self.storage, self.policy, self.clock = session, storage, policy, clock

    def upload(self, principal: Principal | None, purpose: str, content: bytes) -> MediaAssetRecord:
        owner = self.policy.authorize_write(principal, "uploadMedia")
        if purpose not in {"POST", "AVATAR", "COVER"}:
            raise invalid("purpose")
        image = process_image(content)
        asset_id, now = uuid4(), self.clock.now()
        key = f"{asset_id}.jpg"
        try:
            self.storage.store(key, image.content)
        except OSError:
            raise IntegrationError() from None
        asset = MediaAssetRecord(
            id=asset_id,
            owner_id=owner,
            purpose=purpose,
            state="PENDING",
            provider="local",
            storage_key=key,
            url=f"/media/{asset_id}",
            input_size_bytes=len(content),
            stored_size_bytes=len(image.content),
            mime_type="image/jpeg",
            width=image.width,
            height=image.height,
            created_at=now,
            expires_at=now + timedelta(hours=24),
            consumed_at=None,
            deleted_at=None,
        )
        try:
            return TransactionManager(self.session).run(
                lambda: MediaUploadRepository(self.session).create(asset)
            )
        except Exception:
            self.storage.remove(key)
            raise
