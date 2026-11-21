# Backend Content

Python 3.11, PostgreSQL 16; cấu trúc `src/tomateto` giữ từ S8. Xem `db/README.md` tại root repo cho migration/seed và môi trường DB test biệt lập.

Từ root repo:

```powershell
python -m pip install -r db/requirements.lock
python -m pip install --no-build-isolation -e backend
alembic -c db/alembic.ini upgrade head
uvicorn tomateto.bootstrap.run_content:build_app --factory
```

Thiết lập DATABASE_URL, MEDIA_ROOT và CORS_ORIGINS từ môi trường. File mẫu không được tự động nạp. MEDIA_ROOT cần lưu bền vững và dùng chung giữa API/worker; không mount public static.

API thành phần Content: POST `/graphql`, POST `/media/uploads`, GET `/media/{uuid}`. Entry point mặc định cho Guest đọc feed; mọi token bị từ chối tới khi nhóm Identity cung cấp `SessionVerifier` thực. Để tích hợp, gọi `create_app` với `verifier_factory`, B10 `policy`, session factory và storage root. Test dùng verifier tiêm riêng, không bỏ xác thực trong sản phẩm.

GraphQL Content là schema thành phần để ghép với các nhóm khác. Hợp đồng cursor/lỗi/transaction nhận từ BE S8, được chuyển import về package chuẩn. Không tạo thêm metadata cho Chat/Trending cạnh metadata 25 bảng.

```powershell
python -m pytest -c backend/pyproject.toml -q
python -m ruff check backend db --config backend/pyproject.toml
python -m mypy --config-file backend/pyproject.toml
```

Hoặc `docker compose -f db/compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests`. Đây là Compose test, không thay môi trường triển khai chung của Lead.
