# Giao việc S7 cho thành viên: test case, chuẩn code, review WBS

Ngày: 11/11/2026. Người giao: Lead. Hạn chung: **trước buổi họp Chủ nhật 15/11/2026**, mở PR một DOC một nhánh theo quy ước của nhóm; reviewer là vai khác vai viết, đọc và góp ý trên PR trong 3 ngày.

Tài liệu đã có để bám: DOC 7.3-A (kế hoạch kiểm thử), DOC 7.3-C (ma trận phủ UC và dải ID), DOC 7.4-A (chuẩn chung), DOC 7.4-B (cấu hình), DOC 7.5-A (WBS chính thức), DOC 7.2-A tổng hợp (mã lỗi). Hạn của từng việc ở bảng cuối.

## 1. Việc 7.1.2, 7.1.3, 7.1.4: test case

| Việc | Người viết | Tệp DOC | Reviewer |
|---|---|---|---|
| 7.1.2 Test case backend | BE | `7.3-A.1_test_case_be.md` | FE |
| 7.1.3 Test case frontend | FE | `7.3-A.2_test_case_fe.md` | DB |
| 7.1.4 Test case dữ liệu | DB | `7.3-A.3_test_case_db.md` | BE |

**Mẫu:** mỗi test case đúng các trường ở DOC 7.3-A mục 7 (ID, tên, truy vết, mức, điều kiện đầu, bước, kết quả mong đợi). Một bảng cho mỗi UC, tiêu đề bảng là mã và tên UC theo DOC 2.1-B.

**Phạm vi bắt buộc cho mỗi vai:**
1. Đủ 12 UC mức Must của DOC 7.3-C (UC-01…UC-10, UC-13, UC-14): ca chính và ít nhất một ca lỗi, đúng số ID đã cấp trong DOC 7.3-C (ca chính số 01, ca lỗi từ số 02).
2. Các UC Should và Could: ít nhất ca chính, nếu vai đó có dải ID ở DOC 7.3-C.
3. Các NFR của vai mình theo DOC 7.3-A mục 6 (cột "Vai"): mỗi NFR một test case, ID dạng `TC-<vai>-N<NFR hai số><số thứ tự>`.
4. Ca lỗi lấy mã lỗi và thông điệp từ DOC 7.2-A (BE mục 3, FE bảng xử lý); mỗi ca lỗi ghi đúng mã và tình huống.

**Việc riêng từng vai:**
- BE: ca ở mức U (thuật toán feed theo con trỏ, xu hướng, quán gần, quay món theo DOC 7.1-A) và mức I (mỗi thao tác GraphQL của UC Must); phân quyền ba loại token (khách, `user_a`, `user_b`).
- FE: ca ở mức E trên Chrome và trình giả lập Android 360 dp; ca mức M ghi vùng chạm, tương phản, đếm thao tác; ca hiển thị lỗi theo từng dòng của DOC 7.2-A FE, trừ các dòng còn lỗ hổng ở DOC 7.2-A tổng hợp.
- DB: ca mức D cho ràng buộc, chỉ mục và truy vấn của thuật toán; ca khôi phục từ bản sao lưu (NFR-11); kịch bản nạp dữ liệu kiểm theo DOC 7.3-A mục 4.

**Ví dụ một dòng đạt:** `TC-BE-0902 | Xoá bài của người khác | UC-09, NFR-07, FORBIDDEN (OWNER_REQUIRED) | I | user_a có bài P1; đăng nhập user_b | 1. gọi xoá P1 bằng token user_b | trả FORBIDDEN, bài P1 vẫn hiển thị ở feed`.

**Ví dụ một dòng không đạt:** "Kiểm tra xoá bài hoạt động tốt" (thiếu dữ liệu, bước, kết quả đo được, truy vết).

**Điều cấm:** không sao chép nguyên văn mô tả UC thành test case; không để ô "Kết quả mong đợi" trống hoặc ghi "đúng yêu cầu"; không đổi dải ID của DOC 7.3-C (cần thêm dải thì nhắn Lead).

**Done khi:** (1) mỗi UC Must có ít nhất hai test case (một chính, một lỗi) trong đúng dải ID; (2) `grep -cE "^\| *TC-<VAI>-[0-9N]" <tệp>` không nhỏ hơn số ở cột "Tối thiểu" của bảng cuối; (3) mỗi test case có truy vết UC hoặc NFR; (4) không có trường trống.

## 2. Việc 7.2.2, 7.2.3, 7.2.4: chuẩn riêng từng vai

| Việc | Người viết | Tệp DOC | Reviewer |
|---|---|---|---|
| 7.2.2 Chuẩn code frontend | FE | `7.4-A.1_chuan_code_fe.md` | BE |
| 7.2.3 Chuẩn code backend | BE | `7.4-A.2_chuan_code_be.md` | DB |
| 7.2.4 Chuẩn đặt tên bảng và migration | DB | `7.4-A.3_chuan_dat_ten_db.md` | FE |

**Mẫu và nội dung:** mỗi tệp có (a) quy tắc đặt tên (tệp, lớp, hàm, biến; FE theo Dart, BE theo Python, DB theo PostgreSQL); (b) cấu trúc thư mục khớp DOC 5.1 và DOC 6.1-A của vai mình; (c) quy tắc lint cụ thể: FE dùng quy tắc trong `analysis_options.yaml` của DOC 7.4-B, BE dùng ruff và mypy cấu hình trong `pyproject.toml` của DOC 7.4-B, DB dùng quy ước đặt tên bảng, cột, khoá, chỉ mục khớp DOC 5.3-B; (d) quy tắc xử lý lỗi và log khớp DOC 7.2-A của vai mình; (e) một bảng "đúng và sai" với ít nhất 5 cặp ví dụ lấy từ mã hoặc lược đồ của ToMateTo.

**Điều cấm:** không chép lý thuyết từ sách (nguyên tắc SOLID chung chung, định nghĩa clean code); không nhắc quy tắc không có công cụ kiểm hoặc không có ví dụ; không nhắc lại phần chuẩn chung của DOC 7.4-A (nhánh, commit, PR, Done).

**Done khi:** (1) mỗi quy tắc có ví dụ đúng hoặc sai; (2) FE chạy được `flutter analyze` trên một tệp mẫu nằm trong tệp DOC; BE chạy được `ruff check --config pyproject.toml` trên tệp mẫu; DB cung cấp một lệnh hoặc truy vấn kiểm tên bảng và cột chạy được trên lược đồ 5.3-B; (3) đủ 5 cặp đúng và sai.

## 3. Việc 7.3.2: review WBS chính thức

**Người làm:** BE. **Đối tượng:** DOC 7.5-A (WBS chính thức), DOC 7.5-B (lịch), DOC 7.5-C (rủi ro). **Cách làm:** bình luận trên PR của Lead, theo quy ước góp ý của nhóm: mỗi ý nêu vị trí và nêu sai gì, không viết hộ nội dung. Đọc kỹ và trả lời hai câu: (a) ngày nộp, số ngày trễ, PR ở cột thực tế của 7.5-A có đúng với những gì BE biết về phần của mình không; (b) các việc BE phải làm ở S8–S11 trong lịch điều chỉnh của 7.5-B có làm được trong thời gian đó không, vì sao. Thêm ít nhất 2 câu hỏi "tại sao" về 7.5-C.

**Done khi:** góp ý đăng trên PR, mỗi ý có vị trí, có trả lời hai câu hỏi (a) và (b).

## 4. Hạn và số lượng tối thiểu

| Việc | Hạn mở PR | Hạn review xong | Tối thiểu |
|---|---|---|---|
| 7.1.2 Test case backend | 15/11/2026 | 18/11/2026 | 12 UC Must × 2 ca + một ca cho mỗi NFR có BE ở cột "Vai" của DOC 7.3-A mục 6 |
| 7.1.3 Test case frontend | 15/11/2026 | 18/11/2026 | 12 UC Must × 2 ca + một ca cho mỗi NFR có FE ở cột "Vai" của DOC 7.3-A mục 6 |
| 7.1.4 Test case dữ liệu | 15/11/2026 | 18/11/2026 | mỗi UC có dải TC-DB × 1 ca + một ca cho mỗi NFR có DB ở cột "Vai" của DOC 7.3-A mục 6 |
| 7.2.2 Chuẩn code frontend | 15/11/2026 | 18/11/2026 | 5 cặp đúng và sai |
| 7.2.3 Chuẩn code backend | 15/11/2026 | 18/11/2026 | 5 cặp đúng và sai |
| 7.2.4 Chuẩn đặt tên DB | 15/11/2026 | 18/11/2026 | 5 cặp đúng và sai |
| 7.3.2 Review WBS | 15/11/2026 | 15/11/2026 | 2 câu trả lời và 2 câu hỏi "tại sao" |
