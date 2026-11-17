# syntax=docker/dockerfile:1
# Image backend ToMateTo (SPEC S8 r2 mục 5): Python 3.12, multi-stage.
# Build context là GỐC repo (xem docker-compose.yml) nhưng image chỉ chứa `backend/`.
# Không copy `.env` vào image: cấu hình đi qua biến môi trường của compose.

# ---------- builder ----------
FROM python:3.12-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
# Cài dependency + package trước để tận dụng cache layer khi mã đổi.
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
RUN pip install --no-cache-dir ./backend

# ---------- runtime ----------
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PYTHONPATH=/srv/backend \
    UPLOAD_DIR=/srv/uploads

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv
# Chỉ `backend/` — bản r2 không có `db/`, không chạy migration (chưa có Alembic).
COPY backend ./backend

RUN mkdir -p "$UPLOAD_DIR" \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser "$UPLOAD_DIR" /srv
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
