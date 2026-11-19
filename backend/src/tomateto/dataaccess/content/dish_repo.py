from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tomateto.dataaccess.content.common import snapshot
from tomateto.dataaccess.schema import dishes
from tomateto.domain.content.normalization import normalize_name
from tomateto.domain.content.records import DishRecord


class DishRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_id(self, dish_id: int) -> DishRecord | None:
        row = self.session.execute(select(dishes).where(dishes.c.id == dish_id)).mappings().first()
        return snapshot(DishRecord, row) if row else None

    def find_by_name_normalized(self, name: str) -> DishRecord | None:
        row = (
            self.session.execute(
                select(dishes).where(dishes.c.name_normalized == normalize_name(name))
            )
            .mappings()
            .first()
        )
        return snapshot(DishRecord, row) if row else None

    def upsert(self, name: str) -> DishRecord:
        normalized = normalize_name(name)
        statement = insert(dishes).values(name=name.strip(), name_normalized=normalized)
        # READ COMMITTED: a second SELECT sees the winning committed insert after conflict wait.
        self.session.execute(
            statement.on_conflict_do_nothing(constraint="uq_dishes_name_normalized")
        )
        row = (
            self.session.execute(select(dishes).where(dishes.c.name_normalized == normalized))
            .mappings()
            .one()
        )
        return snapshot(DishRecord, row)
