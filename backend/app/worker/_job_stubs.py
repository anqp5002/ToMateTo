"""STUB diem noi: vai B1/B2/B4/B8 se thay cac dich vu nay."""

from datetime import datetime


class IdentityService:
    def purge_expired_revocations(self, now: datetime) -> int:
        return 0


class PasswordRecoveryService:
    def purge_expired_reset_requests(self, now: datetime) -> int:
        return 0


class PostLifecycleService:
    def cleanup_orphan_media(self, now: datetime) -> int:
        return 0


class DiscoveryService:
    def refresh_trending_snapshot(self, now: datetime) -> int:
        return 0
