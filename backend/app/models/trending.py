"""T20–T23 snapshot mappings; score retains PostgreSQL NUMERIC precision."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, dish_reference, post_reference, tag_reference


class TrendingRun(Base):
    __tablename__ = "trending_runs"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_trending_runs"),
        Index("ix_trending_runs_published", text("published_at DESC"), text("id DESC")),
        CheckConstraint("window_end > window_start", name="ck_trending_runs_window"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    formula_version: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class TrendingPostSnapshot(Base):
    __tablename__ = "trending_post_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "post_id", name="pk_trending_post_snapshots"),
        Index(
            "ix_trending_post_snapshots_ranking", "run_id", text("score DESC"), text("post_id DESC")
        ),
    )

    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "trending_runs.id",
            name="fk_trending_post_snapshots_run_id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            post_reference.c.id,
            name="fk_trending_post_snapshots_post_id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric)


class TrendingDishSnapshot(Base):
    __tablename__ = "trending_dish_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "dish_id", name="pk_trending_dish_snapshots"),
        Index(
            "ix_trending_dish_snapshots_ranking", "run_id", text("score DESC"), text("dish_id DESC")
        ),
    )

    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "trending_runs.id",
            name="fk_trending_dish_snapshots_run_id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    dish_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            dish_reference.c.id,
            name="fk_trending_dish_snapshots_dish_id",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric)


class TrendingTagSnapshot(Base):
    __tablename__ = "trending_tag_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "tag_id", name="pk_trending_tag_snapshots"),
        Index(
            "ix_trending_tag_snapshots_ranking", "run_id", text("score DESC"), text("tag_id DESC")
        ),
    )

    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "trending_runs.id",
            name="fk_trending_tag_snapshots_run_id",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            tag_reference.c.id,
            name="fk_trending_tag_snapshots_tag_id",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric)
