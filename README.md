# ToMateTo

Ứng dụng cộng đồng chia sẻ món ăn và quán ngon, giúp người dùng quyết định "hôm nay ăn gì" nhanh hơn.

Dự án do nhóm 4 người (Lead, FE, BE, DB) thực hiện theo từng sprint, từ phân tích yêu cầu, thiết kế đến cài đặt.

## Dựng môi trường dev bằng một lệnh

Yêu cầu: Docker Desktop đang chạy, `uv` và Python 3.12.

```bash
# 1. Clone
git clone https://github.com/anqp5002/ToMateTo.git && cd ToMateTo

# 2. Tạo .env từ mẫu (giá trị trong mẫu là GIÁ TRỊ GIẢ, đổi khi chạy thật)
cp .env.example .env

# Điền JWT_SECRET (ít nhất 32 byte) và OTP_PEPPER riêng trong .env.
# Sinh từng giá trị: python -c "import secrets; print(secrets.token_urlsafe(32))"
# Không commit .env. Backend dừng lúc startup nếu thiếu cấu hình Identity.

# 3. Dựng PostgreSQL + backend (backend chờ Postgres healthy rồi mới chạy)
docker compose up -d --build

# 4. Kiểm sức khoẻ — in ra {"status":"ok"} và mã 200
curl -s http://localhost:8000/health

# 5. Chạy lint, kiểm kiểu và test của backend
cd backend && uv venv --python 3.12 && uv pip install -e ".[dev]" && ruff check . && ruff format --check . && mypy . && pytest -q
```

Kết quả bước 4:

```json
{"status": "ok"}
```

## Cổng và dịch vụ

| Dịch vụ | Địa chỉ trên máy dev | Ghi chú |
|---|---|---|
| backend (FastAPI) | `http://localhost:8000` | `GET /health`, `POST /graphql` |
| PostgreSQL | `127.0.0.1:5433` | **Chỉ loopback, dành cho dev.** Trong compose backend nối `postgres:5432` |

- PostgreSQL **không** mở cổng ra ngoài; chỉ `127.0.0.1:${POSTGRES_HOST_PORT}` cho máy dev. Compose production không mở 5432.
- Cổng 5433 chọn để không đụng PostgreSQL cài sẵn trên máy (thường 5432). Đổi bằng `POSTGRES_HOST_PORT` trong `.env`.
- CSDL `tomateto_test` dùng cho kiểm thử: `backend/tests/conftest.py` tự `CREATE DATABASE` nếu thiếu (nối vào DB `postgres`). `pytest` chỉ chạy trên PostgreSQL thật, không SQLite/mock.

## Lệnh thường dùng

```bash
docker compose ps                 # trạng thái container
docker compose logs -f backend    # log backend
docker compose down               # dừng, giữ dữ liệu
docker compose down -v            # dừng và XOÁ volume (dựng lại từ đầu)
```

Trên Windows PowerShell, `curl` là alias của `Invoke-WebRequest`; dùng `curl.exe -s http://localhost:8000/health` hoặc `Invoke-RestMethod`.

## Cấu trúc repo

```text
backend/    FastAPI + Strawberry GraphQL, pyproject.toml, tests/
docs/       tài liệu theo sprint
```

Phần nền nhóm 4.1: [Identity và Recovery](backend/app/business/identity/README.md).

## Cách làm việc

- Mỗi tuần làm 2 sprint; họp trực tiếp 1 lần vào Chủ nhật.
- Trong tuần: mỗi thành viên làm task của mình, đẩy lên nhánh riêng và tạo Pull Request; reviewer chéo review và yêu cầu sửa nếu cần.
- Chủ nhật: báo cáo, hỏi đáp, reviewer đánh giá lại rồi merge vào `main`.
- Không commit trực tiếp vào `main`; mọi thay đổi đi qua Pull Request.

## Quy ước nhánh và commit

- Nhánh: `feat|fix|docs|chore/<scope>-<mô-tả>`, scope gồm `fe`, `be`, `db`, `infra`, `docs`.
- Commit: `<type>(<scope>): <mô tả>`, ghi rõ sprint trong phần mô tả.
- Không đưa khóa, mật khẩu hoặc file `.env` thật lên repo. Chỉ commit `.env.example` với giá trị giả.

## Cấu trúc tài liệu

Tài liệu từng sprint nằm trong thư mục `docs/`, được thêm vào qua Pull Request của từng thành viên.
