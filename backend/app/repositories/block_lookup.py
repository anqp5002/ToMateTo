"""Shared lookup until the Lead's BlockRepository is wired."""

from collections.abc import Collection
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session


class BlockLookup(Protocol):
    def list_blocked_user_ids(self, viewer_id: int) -> Collection[int]: ...


class PostgresBlockLookup:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_blocked_user_ids(self, viewer_id: int) -> set[int]:
        statement = text("""
            SELECT blocked_id FROM user_blocks WHERE blocker_id = :viewer_id
            UNION
            SELECT blocker_id FROM user_blocks WHERE blocked_id = :viewer_id
        """)
        return {
            int(user_id) for user_id in self._session.scalars(statement, {"viewer_id": viewer_id})
        }
