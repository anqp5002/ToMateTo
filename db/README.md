# DB S8 — Migration và repository Content

Phạm vi theo `CHI_TIET_DB_4.2_CONTENT.md` WP42-S8.1/S8.2: schema 25 bảng, seed kiểm thử, model và repository của nhóm 4.2. Chưa có API, upload endpoint, worker hoặc Flutter; các phần đó thuộc S9–S11.

## Chạy kiểm thử bằng Docker

Từ root repo, với Docker Engine đang chạy:

```powershell
docker compose -f db/compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker compose -f db/compose.test.yaml down --volumes
```

Compose chỉ dựng Python 3.11 và PostgreSQL 16 cho tests, không mở cổng DB, dùng mạng nội bộ và DB tạm trên tmpfs. Cấu hình `trust` chỉ dành cho mạng kiểm thử này; không phải cấu hình triển khai. Đây không thay Docker Compose backend/GraphQL do Lead/BE phụ trách.

## Chạy trên DB test do nhóm cấp

Cài Python 3.11 và dependency trong venv:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r db/requirements.lock
python -m pip install --no-build-isolation -e backend
```

Đặt `DATABASE_URL` theo dạng `postgresql+psycopg://.../tomateto_s8_test` bằng thông tin do người quản lý môi trường cấp; đặt `ALLOW_TEST_DATABASE_RESET=1` và `SEED_USER_PASSWORD` bằng mật khẩu thử cục bộ, không commit các giá trị này. Không có DB đích mặc định và không tự đọc một file `.env` thật.

```powershell
alembic -c db/alembic.ini upgrade head
python -m db.seeds.seed_test_data --reset
python -m db.scripts.verify_schema --with-seed
python -m pytest -c backend/pyproject.toml -q
python -m ruff check backend db --config backend/pyproject.toml
python -m ruff format --check backend db --config backend/pyproject.toml
python -m mypy --config-file backend/pyproject.toml
```

Lệnh seed mặc định theo quyết định người yêu cầu ngày 16/11/2026:

- Bốn dòng `users`: `user_a`–`user_d`; Guest là request không token, không có dòng `khach` trong DB.
- 100 món, 60 **quán giả ghi nhãn rõ**, tọa độ trong 5 km quanh tâm (21.0285, 105.8542), 200 bài, 150 bài có ảnh, 3 bài ẩn và 1 báo cáo.
- `user_c` ẩn tên công khai; `user_d` chưa có bài. Mật khẩu được băm bcrypt cost 12 từ biến môi trường, không in ra kết quả.
- 150 PNG nhỏ cho liên kết ảnh và bốn tệp đầu vào NFR-05: PNG hợp lệ 9,9 MiB, PNG 10,1 MiB, tệp không phải ảnh, PNG rộng 2000 px. Chưa chứng minh endpoint upload/resize chạy đúng.
- Byte ảnh nằm trong `uploads/media/`, metadata ở PostgreSQL. URL fixture chỉ là dữ liệu nội bộ; chưa có route HTTP phục vụ ảnh ở S8.

`--reset` chỉ được phép khi tên DB kết thúc `_test` và biến cho phép reset đã đặt. Đây là thao tác xóa dữ liệu thử của toàn bộ schema; dùng DB biệt lập. Không reset DB chung của nhóm. Chạy seed lại không có `--reset` là idempotent trên fixture đã nạp, không tự ghi đè dữ liệu đã bị sửa. PK không deferred là arbiter cho seed; không dùng UNIQUE vị trí ảnh deferred trong `ON CONFLICT`.

Nếu sau này có danh sách quán được duyệt, hỗ trợ `--restaurants file --restaurant-file <file.csv>` với cột `name,address,latitude,longitude`; script kiểm tối thiểu 60 tọa độ hợp lệ trong 5 km. File CSV tự nó không chứng minh nguồn quán là thật; cần Lead xác nhận nguồn.

## Migration và nguồn schema

- `migrations/versions/*_initial_content_schema.py`: revision đầu; SQL đóng băng trong `0001_initial_schema.sql`, không đọc lại tài liệu đang sửa lúc migration chạy.
- `source_manifest.json`: commit nguồn, fingerprint SQL và lựa chọn đã chốt. DDL 6.4-B v1.2: 25 bảng, 161 cột, 116 constraint, 70 index; SQLAlchemy metadata giữ cả comment từ dictionary.
- Upgrade tạo `users` trước, tạo `media_assets`, rồi thêm hai FK avatar/cover. Downgrade bỏ hai FK này trước khi drop các bảng theo thứ tự ngược.
- DDL dùng TEXT + CHECK, không có PostgreSQL enum `pricerange`. Không tạo enum ngoài thiết kế.
- Sau `downgrade base`, Alembic giữ `alembic_version` **rỗng**; đây là hành vi chuẩn. Không xóa bảng này bên trong revision. Extension `pg_trgm`/`unaccent` được giữ ở cấp môi trường, không drop extension dùng chung.

## Quy tắc dùng repository

`backend/src/tomateto/dataaccess/content/models.py` ánh xạ sáu entity trên metadata dùng chung `backend/src/tomateto/dataaccess/schema.py`; record/paging value nằm trong `backend/src/tomateto/domain/content/`. `db/schema.py` chỉ re-export metadata cho công cụ DB. Backend runtime không import package công cụ `db`. Không trả đối tượng ORM có lazy loader ra service.

- Caller sở hữu `Session` và transaction, quyết định commit/rollback. Repository không tự commit và không gọi mạng/provider. Mỗi luồng sử dụng Session riêng.
- `PostRepository.find_by_id(..., for_update=True)` giữ khóa đến khi transaction caller kết thúc. Quyền ghi B10 do service kiểm; đọc được row không chứng minh caller có quyền sửa.
- Feed dùng keyset `(created_at,id)`, lọc hidden/block hai chiều trước LIMIT, `first+1`, batch ảnh/like/save trong một SQL. `PageResult` trả dòng đã cắt và cursor từ dòng cuối thực trả. `PageRequest` ở đây là value nội bộ, chưa thay codec chung/API.
- `LATEST` hoạt động ở S8; `TRENDING` báo rõ chưa tích hợp, không âm thầm rơi về latest. Điểm nối Discovery thuộc S10.
- `DishRepository.upsert` dùng UNIQUE khóa chuẩn hóa và `ON CONFLICT DO NOTHING` rồi SELECT lại, theo isolation READ COMMITTED. Không dùng Session chung cho hai request.
- `RestaurantRepository` chỉ tìm danh sách ứng viên/tìm theo ID/tạo. Không tự gộp theo tên hoặc 100 m. `upsert` quán và quy tắc chọn khi nhiều ứng viên **chờ Lead chốt**, theo lựa chọn người yêu cầu.
- `MediaUploadRepository.consume` khóa asset rồi kiểm owner/purpose/PENDING/hạn, cập nhật ATTACHED và consumed_at. Lỗi nội bộ `UploadRejectedError` cần service/mapper BE chuyển thành mã API đã duyệt.
- `MediaCleanupRepository.enqueue` nhận asset đã DELETE_PENDING. Đổi trạng thái và enqueue phải ở cùng transaction caller; gọi provider sau commit. `list_due` là đọc tác vụ đến hạn, **không phải cơ chế claim nhiều worker**; thiết kế v1 một cleanup worker vẫn phải được giữ khi tích hợp.

## Giới hạn nghiệm thu

Xem [báo cáo S8](../docs/bao_cao/REPORT_S8_DB_4.2.md) để biết nguồn đã dùng, kiểm thử thực tế và những hợp đồng còn thiếu. Các nguồn thiết kế đang review không tự trở thành bằng chứng nhóm đã duyệt. Chưa commit/push hoặc gửi thông báo cho Lead chỉ từ việc chạy tests.

## Chuẩn hóa và tích hợp S8

Python dùng snake_case, cấu hình tập trung tại `backend/pyproject.toml`, SQL đi kèm package khi cài đặt. Giữ Python 3.11 theo chuẩn chung Lead và lựa chọn ngày 19/11/2026; chuẩn BE đang ghi 3.12 nên cần nhóm thống nhất trước khi đổi runtime.

Xem [báo cáo S8](../docs/bao_cao/REPORT_S8_DB_4.2.md) để đọc kết quả kiểm chứng và phần còn chờ tích hợp.
