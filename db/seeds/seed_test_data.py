"""Deterministic fixture: four users, guest context, explicitly labeled synthetic restaurants."""

import argparse
import csv
import json
import math
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import bcrypt
from sqlalchemy import Engine, func, select, text
from sqlalchemy.dialects.postgresql import insert
from tomateto.dataaccess.schema import (
    collection_items,
    collections,
    dishes,
    likes,
    media_assets,
    metadata,
    post_images,
    posts,
    reports,
    restaurants,
    users,
)
from tomateto.domain.content.normalization import normalize_name

from db.connection import make_engine, require_test_reset
from db.seeds.image_fixtures import png, write_nfr05_fixtures

CENTER = (21.0285, 105.8542)
NOW = datetime(2026, 11, 16, 12, tzinfo=UTC)
IMAGE_POST_COUNT = 150
PNG = png(1, 1)


def distance_m(lat: float, lon: float) -> float:
    lat0, lon0 = CENTER
    a = (
        math.sin(math.radians(lat - lat0) / 2) ** 2
        + math.cos(math.radians(lat0))
        * math.cos(math.radians(lat))
        * math.sin(math.radians(lon - lon0) / 2) ** 2
    )
    return 2 * 6371000 * math.asin(min(1.0, math.sqrt(a)))


def restaurant_fixture(kind: str, file: Path | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if kind == "synthetic":
        for i in range(1, 61):
            angle = i * 2 * math.pi / 60
            radius = 1000 + 50 * i
            lat = CENTER[0] + math.degrees(radius * math.cos(angle) / 6371000)
            lon = CENTER[1] + math.degrees(
                radius * math.sin(angle) / (6371000 * math.cos(math.radians(CENTER[0])))
            )
            rows.append(
                {
                    "id": i,
                    "name": f"Quán kiểm thử {i:03}",
                    "address": "DỮ LIỆU GIẢ — không phải địa chỉ quán thật",
                    "latitude": lat,
                    "longitude": lon,
                }
            )
    elif kind == "file" and file is not None:
        with file.open(encoding="utf-8-sig", newline="") as handle:
            for i, row in enumerate(csv.DictReader(handle), 1):
                rows.append(
                    {
                        "id": i,
                        "name": row["name"],
                        "address": row["address"],
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                    }
                )
    else:
        raise ValueError("Select synthetic test coordinates or supply a sourced CSV file")
    if len(rows) < 60:
        raise ValueError("Need at least 60 restaurant coordinates")
    for row in rows:
        lat, lon = float(str(row["latitude"])), float(str(row["longitude"]))
        if (
            not math.isfinite(lat)
            or not math.isfinite(lon)
            or not -90 <= lat <= 90
            or not -180 <= lon <= 180
            or distance_m(lat, lon) > 5000
        ):
            raise ValueError("Restaurant coordinate is invalid or outside the 5 km test fixture")
        row["name_normalized"] = normalize_name(str(row["name"]))
    return rows


def seed(
    engine: Engine,
    *,
    restaurant_kind: str = "synthetic",
    password: str,
    media_dir: Path,
    reset: bool = False,
    restaurant_file: Path | None = None,
) -> dict[str, object]:
    if len(password) < 6 or len(password.encode()) > 72:
        raise ValueError("Test password must fit bcrypt and contain at least six characters")
    data = restaurant_fixture(restaurant_kind, restaurant_file)
    if reset:
        require_test_reset()
    # Images are fixtures only; no public media route/provider is claimed to exist in S8.
    fixture_dir = media_dir / "fixture"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, IMAGE_POST_COUNT + 1):
        (fixture_dir / f"{i:03}.png").write_bytes(PNG)
    write_nfr05_fixtures(media_dir / "nfr05")
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    with engine.begin() as connection:
        if reset:
            # Explicit *_test reset only. Remove cyclic references before ordered deletes.
            connection.execute(users.update().values(avatar_media_id=None, cover_media_id=None))
            connection.execute(text("DELETE FROM chat_messages WHERE role = 'assistant'"))
            for table in reversed(metadata.sorted_tables):
                connection.execute(table.delete())
        account_rows = [
            {
                "id": i,
                "email": f"user_{letter}@example.invalid",
                "email_normalized": f"user_{letter}@example.invalid",
                "password_hash": password_hash,
                "display_name": f"User {letter}",
                "public_profile_fields": ["bio"] if letter == "c" else ["displayName"],
                "created_at": NOW,
                "updated_at": NOW,
            }
            for i, letter in enumerate("abcd", 1)
        ]
        for table, batch in (
            (users, account_rows),
            (
                dishes,
                [
                    {
                        "id": i,
                        "name": f"Món kiểm thử {i:03}",
                        "name_normalized": normalize_name(f"Món kiểm thử {i:03}"),
                        "is_seed": True,
                    }
                    for i in range(1, 101)
                ],
            ),
            (restaurants, data),
            (
                collections,
                [
                    {
                        "id": i,
                        "user_id": i,
                        "name": "Đã lưu",
                        "name_normalized": "da luu",
                        "is_default": True,
                    }
                    for i in range(1, len(account_rows) + 1)
                ],
            ),
            (
                posts,
                [
                    {
                        "id": i,
                        "user_id": 1 + (i % 3),
                        "dish_id": 1 + (i % 100),
                        "restaurant_id": 1 + (i % 60),
                        "caption": f"Bài kiểm thử {i:03}",
                        "is_hidden": i in (198, 199, 200),
                        "created_at": NOW - timedelta(minutes=i // 10),
                        "updated_at": NOW,
                    }
                    for i in range(1, 201)
                ],
            ),
            (
                media_assets,
                [
                    {
                        "id": UUID(int=i),
                        "owner_id": 1 + (i % 3),
                        "purpose": "POST",
                        "state": "ATTACHED",
                        "provider": "local-fixture",
                        "storage_key": f"fixture/{i:03}.png",
                        "url": f"/media/fixture/{i}",
                        "input_size_bytes": len(PNG),
                        "stored_size_bytes": len(PNG),
                        "mime_type": "image/png",
                        "width": 1,
                        "height": 1,
                        "created_at": NOW - timedelta(hours=1),
                        "expires_at": NOW + timedelta(hours=23),
                        "consumed_at": NOW,
                    }
                    for i in range(1, IMAGE_POST_COUNT + 1)
                ],
            ),
            (
                post_images,
                [
                    {"id": i, "post_id": i, "media_id": UUID(int=i), "position": 0}
                    for i in range(1, IMAGE_POST_COUNT + 1)
                ],
            ),
            (likes, [{"user_id": 1, "post_id": 1}, {"user_id": 2, "post_id": 1}]),
            (collection_items, [{"collection_id": 1, "post_id": 1}]),
            (
                reports,
                [
                    {
                        "id": 1,
                        "reporter_id": 1,
                        "post_id": 2,
                        "original_post_id": 2,
                        "reason": "Báo cáo kiểm thử",
                        "evidence_snapshot": {
                            "originalPostId": 2,
                            "authorId": 3,
                            "dishName": "Món kiểm thử 003",
                            "caption": "Bài kiểm thử 002",
                            "capturedAt": NOW.isoformat(),
                        },
                    }
                ],
            ),
        ):
            connection.execute(
                insert(table).values(batch).on_conflict_do_nothing(constraint=table.primary_key)
            )
        for table in metadata.tables.values():
            for column in table.columns:
                if column.identity is not None:
                    # Identifiers are hard-coded in metadata, never user input.
                    sequence = connection.execute(
                        text("SELECT pg_get_serial_sequence(:table, :column)"),
                        {"table": table.name, "column": column.name},
                    ).scalar_one()
                    maximum = connection.execute(select(func.max(column))).scalar_one()
                    connection.execute(
                        text("SELECT setval(CAST(:sequence AS regclass), :value, :called)"),
                        {
                            "sequence": sequence,
                            "value": maximum or 1,
                            "called": maximum is not None,
                        },
                    )
    return {
        "guest_mode": "context_only_no_user_row",
        "guest_authentication": "no token; never inferred from user ID",
        "restaurant_fixture": restaurant_kind,
        "restaurants": len(data),
        "users": len(account_rows),
        "posts": 200,
        "dishes": 100,
        "posts_with_images": IMAGE_POST_COUNT,
        "synthetic_coordinates": restaurant_kind == "synthetic",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--restaurants", choices=("synthetic", "file"), default="synthetic")
    parser.add_argument("--restaurant-file", type=Path)
    args = parser.parse_args()
    password = os.environ.get("SEED_USER_PASSWORD")
    if password is None:
        raise RuntimeError("Set SEED_USER_PASSWORD locally; it will never be printed")
    engine = make_engine()
    try:
        print(
            json.dumps(
                seed(
                    engine,
                    restaurant_kind=args.restaurants,
                    password=password,
                    reset=args.reset,
                    restaurant_file=args.restaurant_file,
                    media_dir=Path(os.environ.get("FIXTURE_MEDIA_DIR", "uploads/media")),
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
