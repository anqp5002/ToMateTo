"""One service-owned transaction and its isolated after-commit callbacks."""

import logging
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")
logger = logging.getLogger(__name__)


class TransactionManager:
    def __init__(self, session: Session) -> None:
        self.session = session
        self._callbacks: list[Callable[[], None]] = []
        self._running = False

    def after_commit(self, callback: Callable[[], None]) -> None:
        if not self._running:
            raise RuntimeError("After-commit work must be registered inside run().")
        self._callbacks.append(callback)

    def run(self, callback: Callable[[], T]) -> T:
        if self._running:
            raise RuntimeError("Nested transaction boundaries are not supported.")
        self._running = True
        try:
            result = callback()
            self.session.commit()
        except BaseException:
            self.session.rollback()
            self._callbacks.clear()
            raise
        finally:
            self._running = False
        callbacks, self._callbacks = self._callbacks, []
        for after_commit in callbacks:
            try:
                after_commit()
            except Exception:
                # Callback failures cannot undo committed data or expose provider details.
                logger.warning("after_commit_failed", extra={"event": "after_commit_failed"})
        return result
