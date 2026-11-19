"""Inspect the migrated catalog and optional seed; never create/alter schema."""

import argparse
import json

from sqlalchemy import Engine, func, inspect, select, text
from tomateto.dataaccess.schema import metadata, post_images, posts, restaurants

from db.connection import make_engine
from db.seeds.seed_test_data import distance_m


def verify_schema(engine: Engine, *, with_seed: bool = False) -> dict[str, object]:
    inspector = inspect(engine)
    actual = set(inspector.get_table_names(schema="public")) - {"alembic_version"}
    if actual != set(metadata.tables):
        raise AssertionError("Catalog does not contain exactly the expected 25 application tables")
    columns = sum(len(inspector.get_columns(name)) for name in actual)
    if columns != 161:
        raise AssertionError("Expected 161 columns")
    with engine.connect() as connection:
        counts = (
            connection.execute(
                text("""
            SELECT (SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
                    JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public'
                    AND t.relname <> 'alembic_version') AS constraints,
                   (SELECT count(*) FROM pg_indexes WHERE schemaname='public'
                    AND tablename <> 'alembic_version') AS indexes
        """)
            )
            .mappings()
            .one()
        )
        if counts["constraints"] != 116 or counts["indexes"] != 70:
            raise AssertionError("Expected 116 constraints and 70 indexes")
        result: dict[str, object] = {"tables": len(actual), "columns": columns, **dict(counts)}
        if with_seed:
            seeded = {
                name: connection.execute(select(func.count()).select_from(table)).scalar_one()
                for name, table in metadata.tables.items()
            }
            image_posts = connection.execute(
                select(func.count(func.distinct(post_images.c.post_id)))
            ).scalar_one()
            coords = connection.execute(
                select(restaurants.c.latitude, restaurants.c.longitude)
            ).all()
            within = sum(
                1
                for lat, lon in coords
                if lat is not None and lon is not None and distance_m(lat, lon) <= 5000
            )
            hidden = connection.execute(
                select(func.count()).select_from(posts).where(posts.c.is_hidden)
            ).scalar_one()
            if (
                seeded["posts"] < 200
                or seeded["dishes"] < 100
                or image_posts < 150
                or within < 60
                or hidden < 3
                or seeded["reports"] < 1
            ):
                raise AssertionError("Seed does not meet required test fixture counts")
            result.update(
                seed_counts=seeded,
                posts_with_images=image_posts,
                restaurants_within_5km=within,
                hidden_posts=hidden,
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-seed", action="store_true")
    args = parser.parse_args()
    engine = make_engine()
    try:
        print(json.dumps(verify_schema(engine, with_seed=args.with_seed), indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
