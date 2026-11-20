"""Read-only discovery queries. All caller input is bound as SQL parameters."""

import hashlib
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from unicodedata import normalize

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import FieldError, ValidationError
from app.core.pagination import CursorCodec, PageRequest, SearchCursor
from app.repositories.block_lookup import BlockLookup, PostgresBlockLookup
from app.repositories.page import RepositoryPage

SearchKind = Literal["DISH", "RESTAURANT", "POST"]
NEARBY_CANDIDATES_SQL = """
    SELECT id,name,latitude,longitude FROM restaurants
    WHERE latitude BETWEEN :min_lat AND :max_lat
      AND longitude IS NOT NULL
      AND (:all_longitudes OR
           (:min_lon<=:max_lon AND longitude BETWEEN :min_lon AND :max_lon) OR
           (:min_lon>:max_lon AND (longitude>=:min_lon OR longitude<=:max_lon)))
    ORDER BY id
"""


def nearby_parameters(
    latitude: float, longitude: float, radius_meters: int
) -> dict[str, float | bool]:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180) or radius_meters <= 0:
        message = "Vị trí chưa hợp lệ. Vui lòng thử lại."
        raise ValidationError(
            message=message, field_errors=[FieldError("location", "LOCATION_INVALID", message)]
        )
    angular_radius = radius_meters / 6_371_000
    latitude_delta = math.degrees(angular_radius)
    min_lat = max(-90.0, latitude - latitude_delta)
    max_lat = min(90.0, latitude + latitude_delta)
    all_longitudes = min_lat <= -90 or max_lat >= 90
    longitude_delta = (
        180.0
        if all_longitudes
        else math.degrees(
            math.asin(min(1.0, math.sin(angular_radius) / math.cos(math.radians(latitude))))
        )
    )
    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": (longitude - longitude_delta + 180) % 360 - 180,
        "max_lon": (longitude + longitude_delta + 180) % 360 - 180,
        "all_longitudes": all_longitudes,
    }


@dataclass(frozen=True)
class SearchHit:
    kind: str
    item_id: int
    title: str
    relevance: int
    type_rank: int


@dataclass(frozen=True)
class NearbyCandidate:
    restaurant_id: int
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class TrendingDishCandidate:
    dish_id: int
    name: str
    score: Decimal


class SearchRepository:
    def __init__(self, session: Session, block_lookup: BlockLookup | None = None) -> None:
        self._session = session
        self._codec = CursorCodec()
        self._blocks = block_lookup if block_lookup is not None else PostgresBlockLookup(session)

    def search_dishes(self, query: str, page: PageRequest) -> RepositoryPage[SearchHit]:
        return self.search(query, page, type_filter="DISH")

    def search_restaurants(self, query: str, page: PageRequest) -> RepositoryPage[SearchHit]:
        return self.search(query, page, type_filter="RESTAURANT")

    def search_posts(
        self, query: str, page: PageRequest, viewer_id: int | None
    ) -> RepositoryPage[SearchHit]:
        return self.search(query, page, viewer_id, type_filter="POST")

    def search(
        self,
        query: str,
        page: PageRequest,
        viewer_id: int | None = None,
        *,
        type_filter: SearchKind | None = None,
    ) -> RepositoryPage[SearchHit]:
        normalized = self._session.scalar(
            text(
                "SELECT lower(public.unaccent(btrim("
                "regexp_replace(:query, '[[:space:]]+', ' ', 'g'))))"
            ),
            {"query": normalize("NFC", query)},
        )
        normalized_query = str(normalized)
        filter_key = type_filter or "ALL"
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()
        scope = f"search:{filter_key}:{viewer_id}:{query_hash}"
        key: SearchCursor | None = None
        if page.after is not None:
            decoded = self._codec.decode(page.after, "SEARCH", scope=scope)
            if not isinstance(decoded, SearchCursor):
                raise ValidationError()
            key = decoded
        statement = text("""
            WITH candidates AS (
                SELECT 'DISH' AS kind,1 AS type_rank,d.id,d.name AS title,
                       d.name_normalized AS field1,'' AS field2
                FROM dishes d WHERE :type_filter IN ('ALL','DISH')
                UNION ALL
                SELECT 'RESTAURANT',2,r.id,r.name,r.name_normalized,''
                FROM restaurants r WHERE :type_filter IN ('ALL','RESTAURANT')
                UNION ALL
                SELECT 'POST',3,p.id,d.name,d.name_normalized,
                       lower(public.unaccent(btrim(regexp_replace(
                           normalize(coalesce(p.caption,''), NFC),'[[:space:]]+',' ','g'))))
                FROM posts p JOIN dishes d ON d.id=p.dish_id
                WHERE :type_filter IN ('ALL','POST') AND NOT p.is_hidden
                AND p.user_id <> ALL(CAST(:blocked_user_ids AS bigint[]))
            ), ranked AS (
                SELECT *, greatest(
                    CASE WHEN field1=:query THEN 3
                         WHEN starts_with(field1,:query) THEN 2
                         WHEN position(:query IN field1)>0 THEN 1 ELSE 0 END,
                    CASE WHEN field2=:query THEN 3
                         WHEN starts_with(field2,:query) THEN 2
                         WHEN position(:query IN field2)>0 THEN 1 ELSE 0 END
                ) AS relevance FROM candidates
            )
            SELECT kind,type_rank,id,title,relevance FROM ranked
            WHERE relevance>0 AND (CAST(:after_score AS integer) IS NULL
                OR relevance<:after_score
                OR (relevance=:after_score AND (type_rank,id)>(:after_type,:after_id)))
            ORDER BY relevance DESC,type_rank ASC,id ASC LIMIT :limit
        """)
        rows = (
            self._session.execute(
                statement,
                {
                    "type_filter": filter_key,
                    "query": normalized_query,
                    "blocked_user_ids": self._blocked_ids(viewer_id)
                    if filter_key in {"ALL", "POST"}
                    else [],
                    "after_score": key.relevance if key else None,
                    "after_type": key.type_rank if key else None,
                    "after_id": key.item_id if key else None,
                    "limit": page.first + 1,
                },
            )
            .mappings()
            .all()
        )
        items = [
            SearchHit(
                str(r["kind"]),
                int(r["id"]),
                str(r["title"]),
                int(r["relevance"]),
                int(r["type_rank"]),
            )
            for r in rows
        ]
        return RepositoryPage.from_rows(
            items,
            page,
            lambda item: self._codec.encode_search(
                item.relevance, item.type_rank, item.item_id, scope=scope
            ),
        )

    def _blocked_ids(self, viewer_id: int | None) -> list[int]:
        return list(self._blocks.list_blocked_user_ids(viewer_id)) if viewer_id is not None else []

    def find_nearby(
        self, latitude: float, longitude: float, radius_meters: int = 5000
    ) -> list[NearbyCandidate]:
        rows = (
            self._session.execute(
                text(NEARBY_CANDIDATES_SQL), nearby_parameters(latitude, longitude, radius_meters)
            )
            .mappings()
            .all()
        )
        return [
            NearbyCandidate(
                int(r["id"]), str(r["name"]), float(r["latitude"]), float(r["longitude"])
            )
            for r in rows
        ]

    def list_trending_dishes(
        self, limit: int, viewer_id: int | None = None
    ) -> list[TrendingDishCandidate]:
        if limit <= 0:
            raise ValidationError(message="Số lượng mục mỗi trang không hợp lệ.")
        rows = (
            self._session.execute(
                text("""
            SELECT s.dish_id,d.name,s.score FROM trending_dish_snapshots s
            JOIN dishes d ON d.id=s.dish_id
            WHERE s.run_id=(SELECT id FROM trending_runs ORDER BY published_at DESC,id DESC LIMIT 1)
            AND EXISTS (
                SELECT 1 FROM trending_post_snapshots ps JOIN posts p ON p.id=ps.post_id
                WHERE ps.run_id=s.run_id AND p.dish_id=s.dish_id AND NOT p.is_hidden
                AND p.user_id <> ALL(CAST(:blocked_user_ids AS bigint[]))
            ) ORDER BY s.score DESC,s.dish_id DESC LIMIT :limit
        """),
                {"blocked_user_ids": self._blocked_ids(viewer_id), "limit": min(limit, 50)},
            )
            .mappings()
            .all()
        )
        return [
            TrendingDishCandidate(int(r["dish_id"]), str(r["name"]), Decimal(r["score"]))
            for r in rows
        ]
