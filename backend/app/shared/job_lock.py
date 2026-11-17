"""PostgreSQL session-level, nonblocking advisory locks."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


class JobLock:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @contextmanager
    def acquire(self, name: str) -> Iterator[bool]:
        session = self._session_factory()
        acquired = False
        try:
            acquired = bool(
                session.execute(
                    text("SELECT pg_try_advisory_lock(hashtext(:name))"), {"name": name}
                ).scalar_one()
            )
            yield acquired
        finally:
            try:
                if acquired:
                    unlocked = session.execute(
                        text("SELECT pg_advisory_unlock(hashtext(:name))"), {"name": name}
                    ).scalar_one()
                    if not unlocked:
                        session.invalidate()
                        raise RuntimeError("Could not release job lock")
            except Exception:
                session.invalidate()
                raise
            finally:
                session.close()
