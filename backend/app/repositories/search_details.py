"""Batch-load details for search results after filtering by viewer."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.pagination import RepositoryPage
from app.repositories.block_lookup import BlockLookup, PostgresBlockLookup
from app.repositories.search_repo import SearchHit


@dataclass(frozen=True)
class SearchDetails:
    restaurants: list[dict[str, Any]]
    posts: list[dict[str, Any]]
    images: list[dict[str, Any]]
    viewer_id: int | None


class SearchDetailsRepository:
    def __init__(self, session: Session, blocks: BlockLookup | None = None) -> None:
        self._session = session
        self._blocks = blocks if blocks is not None else PostgresBlockLookup(session)

    def load(self, result: RepositoryPage[SearchHit], viewer_id: int | None) -> SearchDetails:
        restaurant_ids = [hit.item_id for hit in result.items if hit.kind == "RESTAURANT"]
        post_ids = [hit.item_id for hit in result.items if hit.kind == "POST"]
        restaurants = (
            self._rows(
                """
            SELECT id,name,address,latitude,longitude FROM restaurants
            WHERE id=ANY(CAST(:ids AS bigint[]))
        """,
                {"ids": restaurant_ids},
            )
            if restaurant_ids
            else []
        )
        blocked = (
            list(self._blocks.list_blocked_user_ids(viewer_id)) if viewer_id is not None else []
        )
        posts = (
            self._rows(
                """
            SELECT p.*,d.name AS dish_name,u.display_name,u.public_profile_fields,
                r.name AS restaurant_name,r.address AS restaurant_address,
                r.latitude AS restaurant_latitude,r.longitude AS restaurant_longitude,
                (SELECT count(*) FROM likes l WHERE l.post_id=p.id) AS like_count,
                CASE WHEN CAST(:viewer AS bigint) IS NULL THEN NULL ELSE
                    EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=:viewer)
                END AS is_liked,
                CASE WHEN CAST(:viewer AS bigint) IS NULL THEN NULL ELSE EXISTS(
                    SELECT 1 FROM collection_items ci JOIN collections c ON c.id=ci.collection_id
                    WHERE ci.post_id=p.id AND c.user_id=:viewer
                ) END AS is_saved
            FROM posts p JOIN dishes d ON d.id=p.dish_id JOIN users u ON u.id=p.user_id
            LEFT JOIN restaurants r ON r.id=p.restaurant_id
            WHERE p.id=ANY(CAST(:ids AS bigint[])) AND NOT p.is_hidden
              AND p.user_id <> ALL(CAST(:blocked AS bigint[]))
              AND (CAST(:viewer AS bigint) IS NULL OR NOT EXISTS (
                  SELECT 1 FROM user_blocks b
                  WHERE (b.blocker_id=:viewer AND b.blocked_id=p.user_id)
                     OR (b.blocker_id=p.user_id AND b.blocked_id=:viewer)
              ))
        """,
                {"ids": post_ids, "viewer": viewer_id, "blocked": blocked},
            )
            if post_ids
            else []
        )
        allowed_ids = [row["id"] for row in posts]
        images = (
            self._rows(
                """
            SELECT pi.id,pi.post_id,pi.position,ma.url
            FROM post_images pi JOIN media_assets ma ON ma.id=pi.media_id
            WHERE pi.post_id=ANY(CAST(:ids AS bigint[])) ORDER BY pi.post_id,pi.position,pi.id
        """,
                {"ids": allowed_ids},
            )
            if allowed_ids
            else []
        )
        return SearchDetails(restaurants, posts, images, viewer_id)

    def _rows(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(row) for row in self._session.execute(text(sql), params).mappings().all()]
