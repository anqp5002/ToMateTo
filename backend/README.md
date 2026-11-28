# Backend S8–S9

Phạm vi gồm khung request, lỗi, transaction, phân trang và WP44-S9.1–S9.3 cho tìm kiếm, xu hướng và trợ lý. Mã dùng thư mục `backend/app/` theo hướng dẫn. Python tối thiểu 3.12, SQLAlchemy đồng bộ và PostgreSQL 16.

## Các operation S9

- `search(query, type, page)` kiểm từ khóa và trả connection gộp món, quán, bài. Cursor giữ từ khóa, bộ lọc và người xem. Lọc block trước khi giới hạn trang.
- `trending(page)` trả `WAITING` khi chưa có run và `READY` khi đã có run. Cursor mang `run_id` để các trang tiếp theo tiếp tục dùng run đã đọc.
- `askAssistant`, `retryAssistant`, `assistantSessions` và `assistantHistory` dùng principal từ cổng Identity. Một câu hỏi gắn với một phản hồi; PENDING được commit trước lời gọi AI, kết quả quá hạn hoặc phiên bản cũ không ghi đè phiên bản mới.
- `make_trending_runner(engine, container).run_scheduled_job("refreshTrendingSnapshot")` chạy một lượt tính trong worker. Scheduler 15 phút do Lead cung cấp.

### Điểm cần ghép trước khi nghiệm thu

Nhóm Identity cần bàn giao bộ xác minh JWT và Lead bàn giao `WriteAuthorizationPolicy` thật. `create_app` nhận `session_verifier_factory` qua container và nhận `write_policy` qua tham số. Nếu thiếu policy, mutation trợ lý từ chối ghi; test dùng bản giả có phạm vi rõ ràng.

Adapter AI nhận endpoint qua `AI_PROVIDER_URL` và `AI_PROVIDER_KEY`, cả hai cùng được đặt hoặc cùng để trống; URL cấu hình phải dùng HTTPS. Adapter yêu cầu đầu vào JSON gồm câu hỏi và các bài công khai, đầu ra có `content`, `postIds`, `dishIds`, `restaurantIds`. Provider thật và hợp đồng phản hồi cần nhóm xác nhận. Cho tới khi xác nhận, service dựng câu trả lời ngắn từ dữ liệu công khai đã kiểm lại; chưa sử dụng nội dung tự do hoặc trích xuất draft từ provider. Draft hợp lệ đã lưu được ánh xạ vào phản hồi GraphQL; luồng dùng draft UC-19 thuộc S10. Nếu provider lỗi, service lưu trạng thái `FALLBACK` hoặc `FAILED` và trả `INTEGRATION_UNAVAILABLE`.

Ngữ cảnh kèm tối đa 10 tin hoàn tất của đúng phiên và 10 bài công khai. Các mẫu email, token và cặp tọa độ được che, nhưng việc nhận diện theo mẫu không bảo đảm loại được toàn bộ thông tin riêng tư từ văn bản tự do. Giới hạn 2.048 token đầu vào / 512 token đầu ra cần tokenizer của model và provider cụ thể. Circuit breaker mặc định tắt vì DOC 7.2-A xem đây là đề xuất chờ duyệt; nếu được duyệt có thể bật bằng `AI_CIRCUIT_BREAKER_ENABLED` và cấu hình ngưỡng lỗi, thời gian thử lại qua `AI_CIRCUIT_FAILURE_THRESHOLD` và `AI_CIRCUIT_RECOVERY_SECONDS` (giá trị mẫu 5 lỗi / 30 giây). Đã kiểm timeout adapter và đường xử lý provider chậm; chưa chứng minh NFR-04 cho toàn request với DB và provider thật.

`CORS_ORIGINS` là danh sách origin web được phép, ngăn cách bằng dấu phẩy. Để trống thì không bật CORS cho origin khác. Job xu hướng mặc định chỉ công bố bài và món theo Q15; `TRENDING_TAGS_ENABLED` mặc định `false`. Chỉ bật snapshot thẻ theo công thức đề xuất DOC 7.1-A sau khi Lead/DB duyệt D07. Retry trạng thái FALLBACK tiếp tục dùng kết quả hiện có theo DOC 5.3-B; chính sách này cần nhóm chốt.

Nếu dữ liệu nguồn thay đổi trước khi công bố xu hướng, worker bỏ lượt và không công bố snapshot dở dang; hiện chưa tự tính lại ngay, sẽ chờ lịch chạy tiếp theo. Cần đối chiếu cơ chế tính lại với Q15 của DB khi tích hợp.

Vị trí gửi trong `askAssistant` chỉ dùng tạm để chọn bài công khai gắn với quán trong bán kính 5 km; không lưu tọa độ vào lịch sử hoặc gửi tọa độ cho provider. Khi thiếu vị trí, `ASSISTANT_DEFAULT_LATITUDE` và `ASSISTANT_DEFAULT_LONGITUDE` mặc định theo điểm seed Hà Nội (21.0285, 105.8542), là giá trị tạm chưa được chốt làm cấu hình sản phẩm. Đổi qua môi trường khi nhóm thống nhất. Khi retry mà không có vị trí mới, dùng vị trí mặc định vì không lưu tọa độ của lần hỏi trước.

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

Các quyết định đang mở về tỷ lệ pool quay món, ngắt mạch và quota cần được chốt trước phần phụ thuộc ở S10. Không ghi tọa độ người dùng vào ngữ cảnh AI hoặc lịch sử.
