import struct
import uuid
from pathlib import Path

import bcrypt
import pytest
from sqlalchemy import Engine, func, select
from tomateto.dataaccess.schema import dishes, posts, users

from db.scripts.verify_schema import verify_schema
from db.seeds.seed_test_data import seed


def test_seed_idempotence_coordinates_images_and_identity(engine: Engine, tmp_path: Path) -> None:
    password = uuid.uuid4().hex
    first = seed(
        engine,
        restaurant_kind="synthetic",
        password=password,
        media_dir=tmp_path,
        reset=True,
    )
    before = verify_schema(engine, with_seed=True)
    again = seed(
        engine,
        restaurant_kind="synthetic",
        password=password,
        media_dir=tmp_path,
    )
    assert first == again
    assert verify_schema(engine, with_seed=True) == before
    counts = before["seed_counts"]
    assert isinstance(counts, dict) and counts["users"] == 4
    assert before["posts_with_images"] == 150
    within = before["restaurants_within_5km"]
    assert isinstance(within, int) and within >= 60
    assert len(list((tmp_path / "fixture").glob("*.png"))) == 150
    png = (tmp_path / "fixture/001.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack("!II", png[16:24]) == (1, 1)
    assert (tmp_path / "nfr05/valid_9_9mb.png").stat().st_size == int(9.9 * 1024**2)
    assert (tmp_path / "nfr05/too_large_10_1mb.png").stat().st_size > 10 * 1024**2
    assert not (tmp_path / "nfr05/not_image.txt").read_bytes().startswith(b"\x89PNG")
    wide = (tmp_path / "nfr05/wide_2000.png").read_bytes()
    assert struct.unpack("!II", wide[16:24]) == (2000, 1)
    with engine.begin() as connection:
        stored = connection.execute(
            select(users.c.password_hash).where(users.c.id == 1)
        ).scalar_one()
        assert bcrypt.checkpw(password.encode(), stored.encode()) and "$12$" in stored
        assert (
            connection.execute(
                select(func.count()).select_from(posts).where(posts.c.user_id == 4)
            ).scalar_one()
            == 0
        )
        fields = connection.execute(
            select(users.c.public_profile_fields).where(users.c.id == 3)
        ).scalar_one()
        assert "displayName" not in fields
        assert (
            connection.execute(
                select(func.count()).select_from(users).where(users.c.id == 4)
            ).scalar_one()
            == 1
        )
        row = connection.execute(
            dishes.insert()
            .values(name="Sequence check", name_normalized="sequence check")
            .returning(dishes.c.id)
        ).scalar_one()
        assert row > 100
        connection.execute(dishes.delete().where(dishes.c.id == row))


def test_seed_reset_guard(engine: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOW_TEST_DATABASE_RESET", raising=False)
    with pytest.raises(RuntimeError, match="Reset needs"):
        seed(
            engine,
            restaurant_kind="synthetic",
            password=uuid.uuid4().hex,
            media_dir=tmp_path,
            reset=True,
        )
