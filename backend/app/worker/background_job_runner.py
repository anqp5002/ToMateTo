"""Dispatch scheduled jobs without sharing sessions or exposing payloads in logs."""

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from app.bootstrap.worker_scope import WorkerScope


class JobStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class JobResult:
    status: JobStatus
    processed: int


class Lock(Protocol):
    def acquire(self, name: str) -> AbstractContextManager[bool]: ...


class BackgroundJobRunner:
    def __init__(self, lock: Lock, scope_factory: Callable[[], WorkerScope]) -> None:
        self._lock = lock
        self._scope_factory = scope_factory
        self.registry: dict[str, Callable[[WorkerScope], int]] = {
            "refreshTrendingSnapshot": lambda s: s.discovery_service.refresh_trending_snapshot(
                datetime.now(UTC)
            ),
            "cleanupOrphanMedia": lambda s: s.post_lifecycle_service.cleanup_orphan_media(
                datetime.now(UTC)
            ),
            "purgeExpiredResetRequests": lambda s: (
                s.password_recovery_service.purge_expired_reset_requests(datetime.now(UTC))
            ),
            "purgeExpiredRevocations": lambda s: s.identity_service.purge_expired_revocations(
                datetime.now(UTC)
            ),
        }

    def run_scheduled_job(self, name: str) -> JobResult:
        if name not in self.registry:
            raise ValueError("Unknown scheduled job")
        result = JobResult(JobStatus.FAILED, 0)
        try:
            with self._lock.acquire(name) as acquired:
                if not acquired:
                    result = JobResult(JobStatus.SKIPPED, 0)
                else:
                    with self._scope_factory() as scope:
                        result = JobResult(JobStatus.SUCCESS, self.registry[name](scope))
        except Exception:
            result = JobResult(JobStatus.FAILED, 0)
        logging.getLogger(__name__).info(
            "job=%s status=%s processed=%d", name, result.status.value, result.processed
        )
        return result
