"""Điểm vào FastAPI của ToMateTo backend.

S8 mới có `/health` (không chạm CSDL) và `/graphql` được thêm ở TASK 3.
"""

from fastapi import FastAPI

app = FastAPI(title="ToMateTo API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Báo backend còn sống. Cố ý không truy vấn CSDL."""
    return {"status": "ok"}
