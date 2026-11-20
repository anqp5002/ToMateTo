"""Exercise the worker lock on PostgreSQL across independent runners."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.core.container import AppContainer, WorkerScope
from app.jobs.runner import BackgroundJobRunner
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker


def test_same_job_only_opens_one_worker_scope(
    db_engine: Engine, session_factory: sessionmaker[Session], container: AppContainer
) -> None:
    entered, release = Event(), Event()
    calls: list[WorkerScope] = []

    def work(scope: WorkerScope) -> int:
        calls.append(scope)
        entered.set()
        assert release.wait(5), "Second runner did not finish."
        return scope.transaction.run(lambda: 3)

    first = BackgroundJobRunner(db_engine, container, {"refreshTrendingSnapshot": work})
    second = BackgroundJobRunner(db_engine, container, {"refreshTrendingSnapshot": work})
    with ThreadPoolExecutor(max_workers=2) as pool:
        task = pool.submit(first.run_scheduled_job, "refreshTrendingSnapshot")
        try:
            assert entered.wait(5), "First job did not start."
            skipped = second.run_scheduled_job("refreshTrendingSnapshot")
            assert skipped.status == "SKIPPED"
            assert len(calls) == 1
        finally:
            release.set()
        result = task.result(timeout=5)
    assert result.status == "SUCCESS" and result.processed == 3
    assert result.duration_seconds >= 0


def test_failed_job_rolls_back_and_lock_is_reusable(
    db_engine: Engine, container: AppContainer
) -> None:
    def failed(scope: WorkerScope) -> int:
        scope.session.execute(text("UPDATE dishes SET name = 'uncommitted' WHERE id = 1"))
        raise RuntimeError("internal provider details")

    runner = BackgroundJobRunner(db_engine, container, {"refreshTrendingSnapshot": failed})
    assert runner.run_scheduled_job("refreshTrendingSnapshot").status == "FAILED"
    with db_engine.connect() as connection:
        assert connection.scalar(text("SELECT name FROM dishes WHERE id = 1")) == "Phở 1"
    next_runner = BackgroundJobRunner(
        db_engine, container, {"refreshTrendingSnapshot": lambda scope: 0}
    )
    assert next_runner.run_scheduled_job("refreshTrendingSnapshot").status == "SUCCESS"


def test_different_job_names_do_not_block_each_other(
    db_engine: Engine, container: AppContainer
) -> None:
    entered, release = Event(), Event()

    def held(scope: WorkerScope) -> int:
        entered.set()
        assert release.wait(5)
        return 0

    runner = BackgroundJobRunner(
        db_engine,
        container,
        {"refreshTrendingSnapshot": held, "purgeExpiredRevocations": lambda scope: 0},
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(runner.run_scheduled_job, "refreshTrendingSnapshot")
        try:
            assert entered.wait(5)
            assert runner.run_scheduled_job("purgeExpiredRevocations").status == "SUCCESS"
        finally:
            release.set()
        assert first.result(timeout=5).status == "SUCCESS"
