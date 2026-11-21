"""Bounded public projections: no account secrets, no lazy loading, no per-post queries."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ImageView:
    id: int
    url: str
    position: int


@dataclass(frozen=True)
class PostView:
    id: int
    user_id: int
    dish_name: str
    caption: str | None
    address: str | None
    price_range: str | None
    feeling: str | None
    latitude: float | None
    longitude: float | None
    ingredients: list[str]
    instructions: list[str]
    created_at: datetime
    updated_at: datetime
    author_name: str | None
    avatar_url: str | None
    restaurant_id: int | None
    restaurant_name: str | None
    restaurant_address: str | None
    restaurant_latitude: float | None
    restaurant_longitude: float | None
    images: list[ImageView]
    like_count: int
    is_liked: bool | None
    is_saved: bool | None


SQL = """
WITH wanted AS (SELECT unnest(CAST(:ids AS bigint[])) AS id),
lc AS (SELECT l.post_id, count(*) AS total FROM likes l JOIN wanted w ON w.id=l.post_id
       GROUP BY l.post_id),
imgs AS (SELECT pi.post_id, jsonb_agg(jsonb_build_object('id',pi.id,'url',ma.url,
    'position',pi.position) ORDER BY pi.position,pi.id) AS items
    FROM post_images pi JOIN wanted w ON w.id=pi.post_id
    JOIN media_assets ma ON ma.id=pi.media_id GROUP BY pi.post_id)
SELECT p.*, d.name AS dish_name,
 CASE WHEN u.id=:viewer OR 'displayName'=ANY(u.public_profile_fields)
      THEN u.display_name END AS author_name,
 CASE WHEN u.id=:viewer OR 'avatarUrl'=ANY(u.public_profile_fields)
      THEN avatar.url END AS avatar_url,
 r.name AS restaurant_name, r.address AS restaurant_address,
 r.latitude AS restaurant_latitude, r.longitude AS restaurant_longitude,
 coalesce(imgs.items,'[]'::jsonb) AS images, coalesce(lc.total,0) AS like_count,
 CASE WHEN CAST(:viewer AS bigint) IS NULL THEN NULL ELSE EXISTS(
   SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=:viewer) END AS is_liked,
 CASE WHEN CAST(:viewer AS bigint) IS NULL THEN NULL ELSE EXISTS(
   SELECT 1 FROM collection_items ci JOIN collections c ON c.id=ci.collection_id
   WHERE ci.post_id=p.id AND c.user_id=:viewer) END AS is_saved
FROM posts p JOIN wanted w ON w.id=p.id JOIN dishes d ON d.id=p.dish_id
JOIN users u ON u.id=p.user_id LEFT JOIN restaurants r ON r.id=p.restaurant_id
LEFT JOIN media_assets avatar ON avatar.id=u.avatar_media_id
LEFT JOIN imgs ON imgs.post_id=p.id LEFT JOIN lc ON lc.post_id=p.id
WHERE (NOT p.is_hidden OR (CAST(:own_hidden AS boolean) AND p.user_id=:viewer))
AND (CAST(:viewer AS bigint) IS NULL OR NOT EXISTS(SELECT 1 FROM user_blocks b
 WHERE (b.blocker_id=:viewer AND b.blocked_id=p.user_id)
 OR (b.blocked_id=:viewer AND b.blocker_id=p.user_id)))
"""


class PostProjection:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read(
        self, ids: list[int], viewer_id: int | None, *, own_hidden: bool = False
    ) -> dict[int, PostView]:
        rows = self.session.execute(
            text(SQL), {"ids": ids, "viewer": viewer_id, "own_hidden": own_hidden}
        ).mappings()
        return {
            row["id"]: PostView(
                **{
                    key: row[key]
                    for key in (
                        "id",
                        "user_id",
                        "dish_name",
                        "caption",
                        "price_range",
                        "feeling",
                        "latitude",
                        "longitude",
                        "created_at",
                        "updated_at",
                        "author_name",
                        "avatar_url",
                        "restaurant_id",
                        "restaurant_name",
                        "restaurant_address",
                        "restaurant_latitude",
                        "restaurant_longitude",
                        "like_count",
                        "is_liked",
                        "is_saved",
                    )
                },
                address=row["location_address"],
                ingredients=row["recipe_ingredients"],
                instructions=row["recipe_steps"],
                images=[ImageView(**image) for image in row["images"]],
            )
            for row in rows
        }

    def allocate_id(self, table: str) -> int:
        if table not in {"posts", "post_images"}:
            raise ValueError("Unsupported identity")
        return int(
            self.session.execute(
                text("SELECT nextval(pg_get_serial_sequence(:table, 'id'))"), {"table": table}
            ).scalar_one()
        )
