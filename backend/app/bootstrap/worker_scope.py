"""One independently owned session and service set per worker execution."""

from typing import Protocol

from app.worker._job_stubs import (
    DiscoveryService,
    IdentityService,
    PasswordRecoveryService,
    PostLifecycleService,
)


class ClosableSession(Protocol):
    def close(self) -> None: ...


class WorkerScope:
    def __init__(self, session: ClosableSession) -> None:
        self.session = session
        self.identity_service = IdentityService()
        self.password_recovery_service = PasswordRecoveryService()
        self.post_lifecycle_service = PostLifecycleService()
        self.discovery_service = DiscoveryService()

    def __enter__(self) -> "WorkerScope":
        return self

    def __exit__(self, *args: object) -> None:
        self.session.close()
