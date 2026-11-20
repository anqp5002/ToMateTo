from collections.abc import Callable

import pytest
from app.core.exceptions import ValidationError
from app.core.transaction import TransactionManager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def test_transaction_returns_result_and_commits_before_callback() -> None:
    engine = create_engine("sqlite://")
    with Session(engine) as session:
        transaction = TransactionManager(session)
        events: list[str] = []

        def operation() -> int:
            session.execute(text("CREATE TABLE sample (id INTEGER)"))
            session.execute(text("INSERT INTO sample VALUES (1)"))
            transaction.after_commit(lambda: events.append("callback"))
            return 7

        assert transaction.run(operation) == 7
        assert events == ["callback"]
        assert not session.in_transaction()


@pytest.mark.parametrize("failure", [ValidationError, RuntimeError])
def test_transaction_rolls_back_and_discards_callbacks(failure: Callable[[], Exception]) -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE sample (id INTEGER)"))
    events: list[str] = []
    with Session(engine) as session:
        transaction = TransactionManager(session)

        def operation() -> None:
            session.execute(text("INSERT INTO sample VALUES (1)"))
            transaction.after_commit(lambda: events.append("should-not-run"))
            raise failure()

        with pytest.raises(type(failure())):
            transaction.run(operation)
        assert session.execute(text("SELECT count(*) FROM sample")).scalar_one() == 0
        assert transaction.run(lambda: 9) == 9
        assert events == []


def test_callback_failure_keeps_committed_transaction(caplog: pytest.LogCaptureFixture) -> None:
    with Session() as session:
        transaction = TransactionManager(session)

        def broken_callback() -> None:
            raise RuntimeError("private provider details")

        def operation() -> int:
            transaction.after_commit(broken_callback)
            return 1

        assert transaction.run(operation) == 1
        assert "after_commit_failed" in caplog.text
        assert "private provider details" not in caplog.text


def test_callback_registration_and_nested_boundaries_are_explicit() -> None:
    with Session() as session:
        transaction = TransactionManager(session)
        with pytest.raises(RuntimeError):
            transaction.after_commit(lambda: None)
        with pytest.raises(RuntimeError):
            transaction.run(lambda: transaction.run(lambda: None))
