from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, update
from sqlalchemy.orm import sessionmaker
from tomateto.bootstrap.content_app import create_app
from tomateto.dataaccess.schema import media_assets, posts

from db.seeds.seed_test_data import seed


def test_all_seed_images_use_protected_routes_and_legacy_repair_is_scoped(
    engine: Engine, tmp_path: Path
) -> None:
    password = uuid4().hex
    seed(engine, password=password, media_dir=tmp_path, reset=True)
    app = create_app(sessionmaker(engine), storage_root=tmp_path)
    with engine.connect() as connection:
        urls = list(connection.scalars(select(media_assets.c.url)))
    assert len(urls) == 150
    with TestClient(app) as client:
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200
            assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
            assert response.headers["content-type"] == "image/png"
        with engine.begin() as connection:
            connection.execute(update(posts).where(posts.c.id == 1).values(is_hidden=True))
        try:
            assert client.get(f"/media/{UUID(int=1)}").status_code == 404
        finally:
            with engine.begin() as connection:
                connection.execute(update(posts).where(posts.c.id == 1).values(is_hidden=False))
    with engine.begin() as connection:
        connection.execute(
            update(media_assets)
            .where(media_assets.c.id == UUID(int=1))
            .values(url="/media/fixture/1")
        )
        connection.execute(
            update(media_assets)
            .where(media_assets.c.id == UUID(int=2))
            .values(url="/custom/edited-fixture")
        )
    seed(engine, password=password, media_dir=tmp_path)
    with engine.connect() as connection:
        assert (
            connection.scalar(select(media_assets.c.url).where(media_assets.c.id == UUID(int=1)))
            == f"/media/{UUID(int=1)}"
        )
        assert (
            connection.scalar(select(media_assets.c.url).where(media_assets.c.id == UUID(int=2)))
            == "/custom/edited-fixture"
        )
        assert connection.scalar(select(func.count()).select_from(media_assets)) == 150
    with engine.begin() as connection:
        connection.execute(
            update(media_assets)
            .where(media_assets.c.id == UUID(int=2))
            .values(url=f"/media/{UUID(int=2)}")
        )
