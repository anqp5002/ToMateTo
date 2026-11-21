"""uvicorn tomateto.bootstrap.run_content:build_app --factory (guest-only until B1 is wired)."""

import os
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tomateto.bootstrap.content_app import create_app


def build_app() -> FastAPI:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return create_app(
        sessionmaker(engine),
        storage_root=Path(os.environ.get("MEDIA_ROOT", "uploads/media")),
        cors_origins=[origin for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin],
    )
