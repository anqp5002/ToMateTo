from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.core.clock import Clock
from app.core.container import AppContainer, WorkerScope
from app.jobs.runner import BackgroundJobRunner
from app.jobs.trending_cron import make_trending_job
from sqlalchemy import Engine, text


def test_two_trending_jobs_publish_once(db_engine: Engine, container: AppContainer) -> None:
    entered, release = Event(), Event()
    job = make_trending_job(Clock())

    def delayed(scope: WorkerScope) -> int:
        entered.set()
        assert release.wait(5)
        return job(scope)

    runner = BackgroundJobRunner(db_engine, container, {"refreshTrendingSnapshot": delayed})
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(runner.run_scheduled_job, "refreshTrendingSnapshot")
        try:
            assert entered.wait(5)
            assert runner.run_scheduled_job("refreshTrendingSnapshot").status == "SKIPPED"
        finally:
            release.set()
        assert future.result(timeout=15).status == "SUCCESS"
    with db_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM trending_runs")) == 1
        connection.execute(text("DELETE FROM trending_runs"))
        connection.commit()
