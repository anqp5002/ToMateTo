from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from tomateto.dataaccess.content.common import snapshot
from tomateto.dataaccess.schema import restaurants
from tomateto.domain.content.normalization import normalize_name
from tomateto.domain.content.records import RestaurantRecord


class RestaurantRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_id(self, restaurant_id: int) -> RestaurantRecord | None:
        row = (
            self.session.execute(select(restaurants).where(restaurants.c.id == restaurant_id))
            .mappings()
            .first()
        )
        return snapshot(RestaurantRecord, row) if row else None

    def find_candidates_by_name(self, name: str) -> list[RestaurantRecord]:
        rows = self.session.execute(
            select(restaurants)
            .where(restaurants.c.name_normalized == normalize_name(name))
            .order_by(restaurants.c.id)
        ).mappings()
        return [snapshot(RestaurantRecord, row) for row in rows]

    def find_by_name_normalized(self, name: str) -> RestaurantRecord | None:
        candidates = self.find_candidates_by_name(name)
        if len(candidates) > 1:
            raise ValueError("Multiple restaurants share this name; select by ID")
        return candidates[0] if candidates else None

    def create(
        self,
        name: str,
        address: str | None = None,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> RestaurantRecord:
        row = (
            self.session.execute(
                insert(restaurants)
                .values(
                    name=name.strip(),
                    name_normalized=normalize_name(name),
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                )
                .returning(restaurants)
            )
            .mappings()
            .one()
        )
        return snapshot(RestaurantRecord, row)
