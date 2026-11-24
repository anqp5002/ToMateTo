"""Điểm vào FastAPI của ToMateTo backend.

Khởi động kiểm cấu hình Identity bắt buộc; `/health` không chạm CSDL.
Router GraphQL nghiệp vụ được tích hợp bởi nhóm API.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.business.identity.config import IdentityConfig


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    application.state.identity_config = IdentityConfig.from_env()
    yield


app = FastAPI(title="ToMateTo API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    """Báo backend còn sống. Cố ý không truy vấn CSDL."""
    return {"status": "ok"}
