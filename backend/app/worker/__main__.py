"""Run jobs at intervals supplied as JSON in JOB_INTERVALS_SECONDS."""

import json
import logging
import os
import time

from app._stubs.db import make_engine, session_factory
from app.bootstrap.worker_scope import WorkerScope
from app.shared.job_lock import JobLock
from app.worker.background_job_runner import BackgroundJobRunner


def main() -> None:
    raw = os.environ.get("JOB_INTERVALS_SECONDS")
    if not raw:
        raise SystemExit("Set JOB_INTERVALS_SECONDS to a JSON object of job names and intervals")
    configured = json.loads(raw)
    if not isinstance(configured, dict) or not configured:
        raise SystemExit("JOB_INTERVALS_SECONDS must be a non-empty object")
    engine = make_engine(os.environ.get("DATABASE_URL"))
    factory = session_factory(engine)
    runner = BackgroundJobRunner(JobLock(factory), lambda: WorkerScope(factory()))
    intervals: dict[str, float] = {}
    for name, value in configured.items():
        if (
            name not in runner.registry
            or isinstance(value, bool)
            or not isinstance(value, int | float)
            or value <= 0
        ):
            raise SystemExit("Invalid job name or interval")
        intervals[name] = float(value)
    logging.basicConfig(level=logging.INFO)
    next_run = {name: time.monotonic() for name in intervals}
    try:
        while True:
            now = time.monotonic()
            for name, deadline in next_run.items():
                if now >= deadline:
                    runner.run_scheduled_job(name)
                    next_run[name] = time.monotonic() + intervals[name]
            time.sleep(max(0, min(next_run.values()) - time.monotonic()))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
