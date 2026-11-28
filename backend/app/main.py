"""Điểm vào FastAPI của ToMateTo backend.

Khởi động kiểm cấu hình Identity bắt buộc; `/health` không chạm CSDL.
Router GraphQL cung cấp các thao tác tài khoản S9.
"""

import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app._stubs.clock import Clock
from app._stubs.db import make_engine, session_factory
from app.business.identity.config import IdentityConfig
from app.business.identity.password_policy import PasswordPolicy
from app.presentation.graphql.auth import router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.identity_config = IdentityConfig.from_env()
    engine = make_engine(os.getenv("DATABASE_URL"))
    application.state.session_factory = session_factory(engine)
    application.state.clock = Clock()
    application.state.dummy_hash = PasswordPolicy().hash(secrets.token_urlsafe(32))
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="ToMateTo API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("WEB_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(
        ","
    ),
    allow_methods=["POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(router, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    """Báo backend còn sống. Cố ý không truy vấn CSDL."""
    return {"status": "ok"}
