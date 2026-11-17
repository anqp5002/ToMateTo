import logging
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Event, Thread
from typing import Any

import pytest
from app.bootstrap.worker_scope import WorkerScope
from app.shared.job_lock import JobLock
from app.worker.background_job_runner import BackgroundJobRunner, JobStatus
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FreeLock:
    @contextmanager
    def acquire(self, name: str) -> Iterator[bool]:
        yield True


def test_success_and_registry(caplog: pytest.LogCaptureFixture) -> None:
    session = FakeSession()
    runner = BackgroundJobRunner(FreeLock(), lambda: WorkerScope(session))
    assert set(runner.registry) == {
        "refreshTrendingSnapshot",
        "cleanupOrphanMedia",
        "purgeExpiredResetRequests",
        "purgeExpiredRevocations",
    }
    runner.registry["refreshTrendingSnapshot"] = lambda scope: 3
    with caplog.at_level(logging.INFO):
        result = runner.run_scheduled_job("refreshTrendingSnapshot")
    assert result.status == JobStatus.SUCCESS and result.processed == 3
    assert session.closed and "SUCCESS" in caplog.text and "3" in caplog.text


def test_failure_closes_session_without_logging_secrets(caplog: pytest.LogCaptureFixture) -> None:
    session = FakeSession()
    runner = BackgroundJobRunner(FreeLock(), lambda: WorkerScope(session))

    def fail(scope: WorkerScope) -> int:
        raise ValueError("secret-token person@example.com")

    runner.registry["cleanupOrphanMedia"] = fail
    with caplog.at_level(logging.INFO):
        result = runner.run_scheduled_job("cleanupOrphanMedia")
    assert result.status == JobStatus.FAILED and result.processed == 0
    assert session.closed and "FAILED" in caplog.text
    assert "secret-token" not in caplog.text and "person@example.com" not in caplog.text


def test_unknown_job() -> None:
    runner = BackgroundJobRunner(FreeLock(), lambda: WorkerScope(FakeSession()))
    with pytest.raises(ValueError):
        runner.run_scheduled_job("unknown")


def test_advisory_lock_concurrent(db_engine: Engine) -> None:
    factory = sessionmaker(bind=db_engine)
    entered, release = Event(), Event()
    calls: list[int] = []
    results: list[Any] = []
    runner = BackgroundJobRunner(JobLock(factory), lambda: WorkerScope(factory()))

    def job(scope: WorkerScope) -> int:
        calls.append(1)
        entered.set()
        assert release.wait(10)
        return 1

    runner.registry["cleanupOrphanMedia"] = job
    thread = Thread(target=lambda: results.append(runner.run_scheduled_job("cleanupOrphanMedia")))
    thread.start()
    try:
        assert entered.wait(10)
        results.append(runner.run_scheduled_job("cleanupOrphanMedia"))
    finally:
        release.set()
        thread.join(timeout=10)
    assert not thread.is_alive()
    assert sorted(result.status.value for result in results) == ["SKIPPED", "SUCCESS"]
    assert calls == [1]
