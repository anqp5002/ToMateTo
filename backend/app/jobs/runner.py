"""Serialize a named job across processes using a PostgreSQL advisory lock."""

import hashlib
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from sqlalchemy import Engine, text

from app.core.container import AppContainer, WorkerScope

logger = logging.getLogger(__name__)
JOB_NAMES = frozenset(
    {
        "refreshTrendingSnapshot",
        "cleanupOrphanMedia",
        "purgeExpiredResetRequests",
        "purgeExpiredRevocations",
    }
)
Job = Callable[[WorkerScope], int]


@dataclass(frozen=True)
class JobResult:
    """Return a safe outcome for the worker process and its logs."""

    name: str
    status: str
    processed: int
    run_id: str
    duration_seconds: float


class BackgroundJobRunner:
    """Open a worker scope only after winning the cross-process job lock.

    The lock uses a separate connection. Service callbacks own their data
    transactions so they can commit, call a provider, then open a new transaction.
    The lock transaction reads no application rows and releases on disconnection.
    """

    def __init__(self, engine: Engine, container: AppContainer, jobs: Mapping[str, Job]) -> None:
        if set(jobs) - JOB_NAMES:
            raise ValueError("Unknown scheduled job.")
        self._engine = engine
        self._container = container
        self._jobs = dict(jobs)

    def run_scheduled_job(self, name: str) -> JobResult:
        """Run a registered service callback or skip if another worker owns it."""
        if name not in self._jobs:
            raise ValueError("Job has not been registered.")
        run_id = str(uuid4())
        started = perf_counter()
        key = int.from_bytes(
            hashlib.sha256(f"tomateto:{name}".encode()).digest()[:8], "big", signed=True
        )
        try:
            with self._engine.begin() as lock_connection:
                acquired = lock_connection.scalar(
                    text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": key}
                )
                if not acquired:
                    return self._result(name, "SKIPPED", 0, run_id, perf_counter() - started)
                with self._container.new_worker_scope() as scope:
                    processed = self._jobs[name](scope)
                    if processed < 0:
                        raise ValueError("Processed count must be nonnegative.")
            return self._result(name, "SUCCESS", processed, run_id, perf_counter() - started)
        except Exception as error:
            # Provider exceptions can contain credentials or private response data.
            return self._result(
                name, "FAILED", 0, run_id, perf_counter() - started, type(error).__name__
            )

    @staticmethod
    def _result(
        name: str,
        status: str,
        processed: int,
        run_id: str,
        duration_seconds: float,
        error_type: str | None = None,
    ) -> JobResult:
        result = JobResult(name, status, processed, run_id, duration_seconds)
        level = logging.ERROR if status == "FAILED" else logging.INFO
        logger.log(
            level,
            "scheduled_job",
            extra={
                "job_name": name,
                "jobRunId": run_id,
                "status": status,
                "processed": processed,
                "duration_seconds": duration_seconds,
                "error_type": error_type,
            },
        )
        return result
