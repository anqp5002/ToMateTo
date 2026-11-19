"""ORM entity mapping; shared metadata includes referenced tables of other groups."""

from sqlalchemy.orm import DeclarativeBase

from tomateto.dataaccess.schema import metadata


class Base(DeclarativeBase):
    metadata = metadata


class Post(Base):
    __table__ = metadata.tables["posts"]


class PostImage(Base):
    __table__ = metadata.tables["post_images"]


class MediaAsset(Base):
    __table__ = metadata.tables["media_assets"]


class Dish(Base):
    __table__ = metadata.tables["dishes"]


class Restaurant(Base):
    __table__ = metadata.tables["restaurants"]


class MediaCleanupJob(Base):
    __table__ = metadata.tables["media_cleanup_jobs"]
