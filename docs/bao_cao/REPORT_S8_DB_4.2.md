# Báo cáo S8 — Nền tảng DB và Content repositories

Ngày triển khai: 16/11/2026; cập nhật: 19/11/2026. Phạm vi: WP42-S8.1 và WP42-S8.2 của hướng dẫn nhóm 4.2; nhánh làm việc `feat/db-s8-content-migration-repositories`.

## 1. Căn cứ

| Nguồn | Phần áp dụng |
|---|---|
| [Hướng dẫn DB S8–S11 tại b58f8ea](https://github.com/anqp5002/ToMateTo/blob/b58f8ea/docs/quan_ly/huong_dan_s8_s11/CHI_TIET_DB_4.2_CONTENT.md), §6 | S8 mở rộng thành schema đầy đủ 25 bảng và repository Content; không chỉ ba bảng đầu như WBS cũ |
| [DOC 6.4-B v1.2 tại 5cfaa56](https://github.com/anqp5002/ToMateTo/blob/5cfaa56ffb4065eb8a60f25dfee5988c1abacb92/docs/thiet_ke/6.4-B_ddl.md), [6.4-A](https://github.com/anqp5002/ToMateTo/blob/5cfaa56ffb4065eb8a60f25dfee5988c1abacb92/docs/thiet_ke/6.4-A_data_dictionary.md) | Bảng/cột, type, default, identity, constraint, index và comment; không thêm bảng nghiệp vụ |
| [HLD 5.3-B v2.3](https://github.com/anqp5002/ToMateTo/blob/461241096bf97eaf33c4593fd76f535c5986f603/docs/thiet_ke/5.3-B_schema_specification.md) | Vòng đời ảnh, transaction, quan hệ và trách nhiệm service/repository |
| [Class BE 6.1-A v1.1](https://github.com/anqp5002/ToMateTo/blob/a0a9e8f79e6ab632befe0dffe04b0007a4e8eb5f/docs/thiet_ke/6.1-A_class_diagrams_backend.md), §4.2 | Tên/phương thức repository và ánh xạ nhóm Content |
| [Query DB S6 tại a15c446](https://github.com/anqp5002/ToMateTo/blob/a15c446/docs/thiet_ke/sql/7.1-A.1_reference_queries.sql), Q02 | Keyset, block hai chiều, batch ảnh/like/save; thêm filter tác giả và danh sách block caller trước LIMIT |
| [Test Plan S7](https://github.com/anqp5002/ToMateTo/blob/26c97c784952c2e97cb32dd38f739a8f5feab6c3/docs/kiem_thu/7.3-A_test_plan.md), §4–6 | Bộ dữ liệu, NFR, DB kiểm riêng; số liệu SQL không thay thời gian API |
| [Chuẩn chung S7](https://github.com/anqp5002/ToMateTo/blob/26c97c784952c2e97cb32dd38f739a8f5feab6c3/docs/quan_ly/7.4-A_chuan_chung.md), [chuẩn DB v1.1](https://github.com/anqp5002/ToMateTo/blob/9a4be45/docs/quan_ly/7.4-A.3_chuan_database_migration.md) | Python 3.11, Sync SQLAlchemy/Psycopg, Alembic, naming, kiểm catalog và dữ liệu |

Các đường dẫn `D:\hdv\...` trong hướng dẫn không tồn tại trên máy này; đã đối chiếu bằng tài liệu tương ứng có commit kiểm soát trong repo. Không sao chép code app mẫu chưa có nội dung. Nhánh DB đã đồng bộ main dfdd097; nguồn S4–S7 hiện có trên main được dùng đối chiếu. Commit trong bảng giữ để truy vết bản thiết kế đã triển khai.

## 2. Kết quả triển khai

| Hạng mục | Đầu ra |
|---|---|
| Migration | Một head Alembic, SQL đóng băng theo 6.4-B; tạo 25 bảng và xử lý vòng users/media; downgrade theo phụ thuộc |
| Metadata/model | 25 bảng, 161 cột, 116 constraint, 70 index; sáu ORM entity Content, record tách Session |
| Seed | Một lệnh reset/nạp; bốn user và Guest không row; 100 món, 60 quán giả trong 5 km, 200 bài, 150 bài có ảnh, 3 bài ẩn, 1 report; bcrypt cost 12, đồng bộ identity sau ID seed |
| Tệp ảnh kiểm | 150 PNG nhỏ và bốn biến thể NFR-05; byte ở filesystem, metadata ở DB, không upload dịch vụ ngoài |
| PostRepository | Save/update/delete/find có khóa, feed và bài tác giả keyset, batch hydration, thay danh sách ảnh; caller điều phối quyền và transaction |
| DishRepository | Chuẩn hóa Việt, upsert an toàn khi hai transaction cùng tạo |
| RestaurantRepository | Tìm theo ID/tên, trả danh sách ứng viên, tạo; không tự gộp và chưa triển khai upsert khi policy chưa chốt |
| MediaUploadRepository | Tạo/tìm/consume có khóa và kiểm lại trạng thái; ghi DELETED cho asset DELETE_PENDING; tìm upload quá hạn |
| MediaCleanupRepository | Enqueue idempotent, đọc job đến hạn, hoàn tất/ghi lần thử lại; không gọi provider hoặc tự cam kết nhiều worker |
| Môi trường test | Docker Compose riêng cho Python 3.11 và PostgreSQL 16; không port DB công khai, không mount dữ liệu sản phẩm |

Các lựa chọn người yêu cầu đã chốt ngày 16/11: 4 user + Guest; dữ liệu quán giả ghi nhãn; không tự gộp quán theo 100 m. Không còn chờ quyết định về ba lựa chọn này. Phạm vi policy upsert quán vẫn chờ Lead đưa quy tắc chính thức.

## 3. Kiểm chứng

Lệnh tái lập và cách đặt biến môi trường ở [db/README.md](../../db/README.md). Chạy soát lại ngày 16/11/2026 trên Python 3.11 và PostgreSQL 16.14, bằng Docker Compose DB mới; **29 tests đạt, 0 lỗi**, thời gian pytest 2,53 giây. `ruff check`, `ruff format --check` và `mypy` đều đạt (22 file nguồn trong phạm vi kiểm kiểu). Không dùng tests S6/S7 làm kết quả S8.

Revision Alembic: `e0c5233f8e90`, một head. Đã kiểm chu kỳ upgrade → downgrade base → upgrade trên DB tạm riêng; catalog đủ 25 bảng/161 cột/116 constraint/70 index và `compare_metadata` không có diff. Mã 55P03 trong phép thử lock timeout là lỗi được kỳ vọng để xác nhận connection thứ hai không lấy được row đang khóa, không phải lỗi test chưa xử lý.

Đã chạy thêm CLI thật trong cùng container kiểm riêng: `alembic upgrade head`, seed có `--reset`, seed lặp không reset, rồi `verify_schema --with-seed`. Kết quả: 4 users, 200 bài, 150 bài gắn ảnh và 150 tệp PNG, 60 quán trong 5 km, 3 bài ẩn; seed hai lần không đổi số lượng. Phép kiểm này kiểm đường vào CLI và tệp ảnh ngoài DB, không chỉ gọi hàm seed từ pytest. Container/mạng test được dọn sau khi lấy kết quả.

**Kết luận soát S8:** WP42-S8.1 và các chức năng repository đã triển khai đạt kiểm thử, sẵn sàng review. Chưa đánh dấu hoàn thiện toàn bộ WP42-S8.2/DoD của S8: `RestaurantRepository.upsert` vẫn chờ policy Lead theo quyết định đã chốt, các điểm nối backend dùng chung chưa được tích hợp và chưa có nội dung “brief mục 5” để chạy bộ kiểm được nhắc trong hướng dẫn. Những mục này không được tính là đã đạt chỉ vì 29 tests hiện có xanh.

Các nhóm kiểm bắt buộc đã được viết: catalog/count/predicate/deferred; metadata không drift; upgrade → downgrade base → upgrade; seed lặp và identity; feed keyset/block/batch; hai transaction tranh UNIQUE món và consume asset; FOR UPDATE chặn connection khác; EXPLAIN kiểm ix_posts_feed mà không tắt Seq Scan; rollback đổi trạng thái/enqueue.

Mã `TC-DB-0801..0804` trong hướng dẫn là nhãn nội bộ của gói S8, không thay nghĩa dải UC-08 trong DOC 7.3-B.3. Đối chiếu kiểm migration/schema với TC-DB-N1401/N1402, feed với TC-DB-0501/0502/0503, consume/race với TC-DB-0703, chuẩn hóa/UNIQUE với TC-DB-2001/2007. Chưa đánh dấu toàn bộ ca S7 đạt vì còn phần service/API/UI.

## 4. Thiếu nguồn, mâu thuẫn và phần chưa nghiệm thu

| Nội dung | Hiện trạng và việc cần từ nhóm |
|---|---|
| `RestaurantRepository.upsert`/gộp quán | Chưa có khóa duy nhất hoặc policy ghép tên/địa chỉ/tọa độ chính thức. Giả thuyết 100 m trong hướng dẫn chưa dùng, theo quyết định người yêu cầu. Lead cần chốt trường nhận diện, xử lý nhiều ứng viên và tranh chấp trước khi thêm upsert. |
| Khung backend dùng chung | Đã có thiết kế lớp/điểm nối, nhưng chưa có mã backend và kiểu Python dùng chung trong workspace để import AccountRepository, WriteAuthorizationPolicy, CursorCodec, ErrorMapper, TransactionManager. Kiểm remote ngày 19/11 thấy FE S8 trong app; chưa thấy implementation BE/Lead S8 cung cấp các điểm nối Python này. S8 dùng Session do caller truyền và paging/record nội bộ; cần BE/Lead/FE nối kiểu và chuyển lỗi, không coi repository là API hoàn chỉnh. |
| “Brief mục 5” và `oteam` | Chưa có brief hoặc nội dung script kiểm mục 5; không thể khẳng định đã chạy bộ kiểm đó. Chưa gửi thông báo cho Lead hoặc dùng lệnh trao đổi trong tài liệu như một lệnh của người yêu cầu. |
| Quán thực/bộ câu hỏi AI | Đã được phép dùng quán giả cho S8. Chưa có danh sách quán thực có nguồn hoặc 20 câu AI được đóng băng; không chứng minh NFR-15 hay dữ liệu địa điểm thực. |
| Hạ tầng toàn dự án | Compose test ở đây không khởi động FastAPI/GraphQL/Flutter; cần cấu hình backend/runtime roles/CI chính thức do Lead/BE cung cấp. |
| Một số dòng trong hướng dẫn | DDL dùng TEXT + CHECK, không có enum `pricerange`. Alembic giữ `alembic_version` rỗng tại base; migration không drop bảng quản lý này giữa chừng. Extension giữ ở cấp môi trường để không xóa tài nguyên chia sẻ. |
| Lifecycle và HTTP | TTL/grace của worker, provider/local storage thật, upload/resize, endpoint và quyền HTTP là phần S9/S10; chưa tự chốt thêm từ các giả thuyết chưa duyệt. |
| Giới hạn vai trò | Repository không xác thực JWT hoặc tự kiểm B10; `list_due` không phải claim nhiều worker. Chưa đo p95 API hoặc cam kết ảnh fixture đã phục vụ được qua HTTP. |

## 5. Bàn giao

Phần có nguồn của S8 được triển khai và kiểm tại DB/repository; những điểm ở mục 4 phải được nhóm xác nhận trước tích hợp tương ứng. Bàn giao trên nhánh S8 riêng để review; chưa mở PR, merge hoặc tuyên bố cả sprint đã được duyệt. Dùng branch `feat/db-s8-content-migration-repositories` cho bước review tiếp theo.

## 6. Chuẩn hóa và kiểm tra nhánh ngày 19/11/2026

- Đồng bộ nền DB với main `dfdd097b9c17e32a2cd58e9b4170a91f71c9f043`.
- Chuyển code sang `backend/src/tomateto/{domain,dataaccess}`, test repository sang `backend/tests/integration/content`, cấu hình sang `backend/pyproject.toml`; bỏ alias camelCase Python. Metadata nằm trong backend để backend không phụ thuộc ngược công cụ DB.
- Đóng gói backend kèm SQL feed; dùng file ignore riêng cho Dockerfile test. Ruff check/format và mypy strict đạt trên Python 3.11, gồm **38 file** nguồn và test.
- Giữ **Python 3.11** theo chuẩn chung Lead và lựa chọn người yêu cầu. Chuẩn BE ghi 3.12: chờ nhóm thống nhất.
- Chạy lại sau chuẩn hóa: **29/29 test đạt**, lượt cuối với dependency build đã khóa: 3,33 giây; CLI migration → seed reset → seed lặp → verify đạt. Xác nhận 4 users, 200 bài, 150 bài có ảnh. Có 153 PNG gồm 150 ảnh bài và 3 ảnh đầu vào NFR; thêm 1 tệp không phải ảnh. Build wheel, kiểm có SQL feed và import runtime từ ngoài repo đều đạt.
- Gộp thử bằng index tạm: cây DB 55 file thay đổi, FE S8 53 file, không trùng đường dẫn, không có unmerged entry tại FE `00c6270a67e599fb29273b5924112a4e9bc346ff`. Không thay index thật, không merge Flutter vào nhánh DB. Kết quả chỉ áp dụng các SHA đã kiểm.
- Xem [mô tả toàn bộ S8](MO_TA_CHI_TIET_S8_DB_4.2.md) cho luồng, trách nhiệm và phần còn chờ.
