"""Callback for the shared BackgroundJobRunner."""

from sqlalchemy import Engine

from app.core.clock import Clock
from app.core.container import AppContainer, WorkerScope
from app.jobs.runner import BackgroundJobRunner, Job
from app.services.trending_service import TrendingService


def make_trending_job(clock: Clock, *, tags_enabled: bool = False) -> Job:
    def run(scope: WorkerScope) -> int:
        return TrendingService(scope.session, clock, tags_enabled=tags_enabled).refresh()

    return run


def make_trending_runner(engine: Engine, container: AppContainer) -> BackgroundJobRunner:
    """Expose one scheduled job to the shared worker process."""
    return BackgroundJobRunner(
        engine,
        container,
        {
            "refreshTrendingSnapshot": make_trending_job(
                container.clock, tags_enabled=container.config.trending_tags_enabled
            )
        },
    )
