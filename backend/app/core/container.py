"""Composition root and bounded SQLAlchemy sessions for requests and jobs."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.config import Config
from app.core.database import create_database_engine, create_session_factory
from app.core.identity import SessionVerifier, UnavailableSessionVerifier
from app.core.transaction import TransactionManager


@dataclass
class RequestScope:
    session: Session
    transaction: TransactionManager
    session_verifier: SessionVerifier


@dataclass
class WorkerScope:
    session: Session
    transaction: TransactionManager


class AppContainer:
    def __init__(
        self,
        config: Config,
        clock: Clock | None = None,
        session_factory: Callable[[], Session] | None = None,
        session_verifier_factory: Callable[[Session], SessionVerifier] | None = None,
    ) -> None:
        self.config = config
        self.clock = clock or Clock()
        self.engine = None
        if session_factory is None:
            self.engine = create_database_engine(config.database_url)
            session_factory = create_session_factory(self.engine)
        self.session_factory = session_factory
        self.session_verifier_factory = session_verifier_factory or (
            lambda session: UnavailableSessionVerifier()
        )

    @contextmanager
    def new_scope(self) -> Iterator[RequestScope]:
        with self.session_factory() as session:
            yield RequestScope(
                session, TransactionManager(session), self.session_verifier_factory(session)
            )

    @contextmanager
    def new_worker_scope(self) -> Iterator[WorkerScope]:
        with self.session_factory() as session:
            yield WorkerScope(session, TransactionManager(session))

    def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()
