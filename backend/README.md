# Backend S8

Phạm vi hiện tại theo WP44-S8.1–S8.3 gồm khung request, lỗi, transaction, phân trang, bộ chạy job và tầng lưu trữ của Khám phá–Trợ lý. Mã dùng thư mục `backend/app/` theo hướng dẫn cài đặt S8. Python tối thiểu 3.11, SQLAlchemy đồng bộ và PostgreSQL 16.

## Chạy và kiểm tra

Từ thư mục gốc repo, tạo môi trường ảo rồi cài dependency.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e "./backend[dev]"
```

Đặt `DATABASE_URL` và `JWT_SECRET` trong môi trường theo `backend/.env.example`. Ứng dụng kiểm hai cấu hình này trước khi nhận request. Sau đó chạy từ thư mục backend.

```powershell
../.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory
```

Gửi `POST /graphql` với body `{"query":"{ __typename }"}`. Kết quả là kiểu gốc `Query`, kèm header `X-Request-Id`. Field `status` kiểm tra khung GraphQL sẵn sàng. Nó chưa xác nhận migration hoặc các chức năng S9 đã sẵn sàng.

Chạy kiểm từ thư mục backend.

```powershell
../.venv/Scripts/python.exe -m ruff check app tests
../.venv/Scripts/python.exe -m ruff format --check app tests
../.venv/Scripts/python.exe -m mypy --no-incremental app tests
../.venv/Scripts/python.exe -m pytest
```

Unit test chạy độc lập. Ca repository và runner cần `TEST_DATABASE_URL` trỏ đến PostgreSQL 16, tên database chứa `test`. Fixture tạo schema tạm, nạp DDL đã commit từ DOC 6.4-B và dữ liệu gồm 200 bài, 30 ảnh, 100 món, 60 quán. Mỗi ca được cô lập bằng rollback. Khi kết thúc, fixture xóa schema tạm của lần chạy. Không truyền URL của database có dữ liệu thật.

## Đối chiếu theo gói S8

- **WP44-S8.1** kiểm query `{ __typename }`, `X-Request-Id`, mã lỗi, commit/rollback và cách ly session. `pytest -k n0701` kiểm phần `ContextFactory` của TC-BE-N0701 bằng cổng Identity giả. Kiểm quyền chủ bài cần service và B10. Các lệnh lint, format, mypy, pytest kiểm phần cục bộ của TC-BE-N1401. Kịch bản máy sạch và CI chờ hạ tầng chung.
- **WP44-S8.2** `pytest -k n0201` kiểm phần kích thước trang của TC-BE-N0201. Các test cursor kiểm thêm trang rỗng, dòng dư, sai loại, sai ngữ cảnh và điểm thập phân. Test nối repository với mapper xác nhận từng edge dùng đúng cursor để đọc tiếp ở trang sau. Kiểm trang sâu qua feed và đo độ trễ phối hợp với DB khi có query feed.
- **WP44-S8.3** các test trên PostgreSQL kiểm `UNIQUE(reply_to_id)`, `CHECK`, cascade, hai lượt tranh quyền xử lý, lọc theo chủ, công bố snapshot và tìm kiếm. Test Q07 dùng `EXPLAIN (FORMAT JSON)` với chính câu SQL và tham số của `find_nearby` trên fixture có bộ lọc địa lý chọn ít dòng. Kiểm phiên sai chủ ở repository là phần dữ liệu của TC-BE-1804 trong DOC 7.3-A.1 hiện tại. Mã lỗi GraphQL được quyết định khi lắp service/resolver. Nhóm DB vẫn chạy TC-DB-2001 ở luồng ghi và tìm với chuẩn hóa chung.

## Điểm nối cho các nhóm

- `SessionVerifier.verify_session(raw_token)` trong `app.core.identity` là cổng nhận bộ xác minh của nhóm Identity. Nhóm đó kiểm chữ ký, hạn, `jti` thu hồi, tài khoản và phiên bản token. `ContextFactory` lấy principal từ cổng này. Khi chưa gắn bản thật, request có Bearer bị từ chối. `SESSION_INVALID` được ghi làm nhãn log, còn mã GraphQL vẫn là `UNAUTHENTICATED`. Bản giả token chỉ nằm trong test.
- `AppContainer.new_scope()` cấp session và `TransactionManager` riêng cho request. `new_worker_scope()` cấp session riêng cho job. Inject các factory và service lúc lắp ghép. Service gọi `run(callback)` để commit hoặc rollback, và đăng ký tác vụ sau commit trong callback đó.
- `CursorCodec` có LATEST, SAVED, TRENDING và SEARCH. TRENDING giữ số thập phân bằng `Decimal`, run ID và target ID. SEARCH thêm khóa relevance theo đặc tả BE mới. Caller dùng `scope` để gắn cursor với loại danh sách, viewer và tiêu chí đọc.
- Repository đưa từng dòng cùng cursor của dòng đó vào `RepositoryPage`. `PageMapper.to_connection(page, node_for)` giữ nguyên cursor và `has_next` khi đổi node sang kiểu trả API. `SearchRepository.search` dùng bộ lọc truy vấn để liên kết cursor, kể cả khi một trang chứa cả món, quán và bài. Giới hạn độ dài từ khóa thuộc service S9.
- `BackgroundJobRunner` nhận các callback từ service của từng nhóm cho bốn tên job đã định nghĩa. Mỗi callback tự dùng transaction của scope. Khóa advisory theo tên được giữ trên connection riêng, chỉ có một worker mở scope thực thi cho cùng job. Runner hiện cung cấp cơ chế chạy một job. Lịch tiến trình worker và các service nghiệp vụ được lắp khi các nhóm bàn giao.
- `SearchRepository`, `TrendingSnapshotRepository`, `AssistantConversationRepository` dùng session caller cấp. Search và Trending cùng nhận `BlockLookup` để nối với `BlockRepository` của Lead. Adapter PostgreSQL tạm giữ hành vi lọc hai chiều trước khi giới hạn kết quả. Khi Lead bàn giao, tiêm implementation đó thay adapter tạm.
- `AssistantConversationRepository.save_message(message, owner_id)` kiểm chủ phiên trước khi ghi câu hỏi. `claim_reply` trả `state` (`CLAIMED`, `BUSY`, `COMPLETED`), `reply_id`, `processing_version` và `current_reply`. `list_sessions` trả dữ liệu tóm tắt gồm `id`, `created_at`, `last_message_at` theo Q22.
- Model BE sở hữu T18–T23 và đăng ký khi import `app.models`. Khai báo ID cho khóa ngoại sang `users`, `posts`, `dishes`, `tags` nằm trong metadata tham chiếu riêng để hỗ trợ kiểm thử độc lập. Alembic của DB cần nạp toàn bộ model chính thức trước khi tự sinh migration. `Base.metadata` của riêng BE chỉ bao phủ sáu bảng.

## Nội dung cần ghép với đầu ra nhóm

Migration Alembic và seed chung có trên nhánh `feat/db-s8-content-migration-repositories`. Kiểm độc lập revision `e0c5233f8e90` trên PostgreSQL 16 đã chạy qua upgrade, downgrade và upgrade lại. Script của DB xác nhận 25 bảng, 161 cột, 116 ràng buộc và 70 chỉ mục. SQL schema trùng DDL mà fixture BE dùng, ngoài cặp lệnh mở và chốt transaction do Alembic đảm nhiệm.

Khi ghép hai nhánh, hợp nhất cấu hình `backend/pyproject.toml` và fixture `backend/tests/conftest.py` để giữ được bộ kiểm của cả hai nhóm. Compose, CI, policy B10, lịch worker và bộ xác minh JWT thật được nối khi Lead và Identity bàn giao.

S8 chưa kích hoạt gọi AI, quay món, job tính điểm, giao diện Flutter hoặc các quyết định đang mở về tỷ lệ pool, ngắt mạch và quota. Repository giữ `OK/FALLBACK` để tái dùng kết quả theo schema hiện tại. Chính sách cho phép retry FALLBACK cần được chốt cùng service trước S9.
