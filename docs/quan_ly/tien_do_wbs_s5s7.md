# Tiến độ WBS S5, S6, S7 — đo ngày 11/11/2026

Trạng thái: **chưa có** · **có nhánh, chưa mở PR** · **PR mở** · **đã merge** · **không đo được từ git**. Nhánh `main` dừng ở commit `393268f` (23/10); chưa có DOC nào của S3 đến S7 vào `main`. Hạn: S5 và S6 là 01/11, S7 là 08/11.

| WBS | Công việc | Vai | Hạn | Trạng thái | Nhánh @SHA | Commit cuối | Ghi chú |
|---|---|---|---|---|---|---|---|
| 5.1.1 | Class diagram backend | BE | 01/11 | PR mở | docs/be-s5-class-design-pr @3571426 | 08/11 | trễ 7 ngày so với hạn; PR #24 |
| 5.1.2 | Class/provider diagram frontend | FE | 01/11 | PR mở | docs/fe-s5-class-sequence @c3b8b46 | 01/11 | đúng hạn; PR #22 |
| 5.1.3 | Review class diagrams | Lead | 01/11 | chưa có | — | — | góp ý đã soạn xong cho PR #22 và #24, chưa đăng lên PR |
| 5.2.1 | Sequence luồng phía backend | BE | 01/11 | PR mở | docs/be-s5-sequence-diagrams @ed27b57 | 03/11 | trễ 7 ngày so với hạn; PR #25 |
| 5.2.2 | Sequence luồng phía frontend | FE | 01/11 | PR mở | docs/fe-s5-class-sequence @c3b8b46 | 01/11 | đúng hạn; PR #22 |
| 5.2.3 | Review sequence | Lead | 01/11 | chưa có | — | — | góp ý đã soạn xong cho PR #22 và #25, chưa đăng lên PR |
| 5.3.1 | Data dictionary + DDL | DB | 01/11 | có nhánh, chưa mở PR | docs/db-s5-data-dictionary-ddl @552c454 | 02/11 | trễ 1 ngày so với hạn |
| 5.3.2 | Review DDL | BE | 01/11 | chưa có | — | — | chưa thấy bình luận nào của BE trên nhánh DB (chưa có PR) |
| 6.1.1 | Mockup hi-fi + design system | FE | 01/11 | PR mở | docs/fe-s6-mockups-error-handling @999e0be | 06/11 | trễ 5 ngày so với hạn; PR #23 |
| 6.1.2 | Review UI | Lead | 01/11 | chưa có | — | — | góp ý đã soạn xong cho PR #23, chưa đăng lên PR |
| 6.2.1 | Đặc tả thuật toán (phân trang feed, xu hướng, gần đây, quay món, gợi ý AI) | BE | 01/11 | PR mở | docs/be-s6-algorithms-error-handling @23a5f14 | 07/11 | trễ 7 ngày so với hạn; PR #26 |
| 6.2.2 | Phần truy vấn/chỉ mục dữ liệu cho các thuật toán | DB | 01/11 | có nhánh, chưa mở PR | docs/db-s6-query-index-algorithms @439472c | 10/11 | trễ 9 ngày so với hạn |
| 6.2.3 | Review thuật toán | Lead | 01/11 | chưa có | — | — | góp ý đã soạn xong cho PR #26 và nhánh DB, chưa đăng lên PR |
| 6.3.1 | Đặc tả xử lý lỗi backend | BE | 01/11 | PR mở | docs/be-s6-algorithms-error-handling @23a5f14 | 07/11 | trễ 7 ngày so với hạn; PR #26 |
| 6.3.2 | Đặc tả xử lý lỗi frontend | FE | 01/11 | PR mở | docs/fe-s6-mockups-error-handling @999e0be | 06/11 | trễ 5 ngày so với hạn; PR #23 |
| 6.3.3 | Tổng hợp + review | Lead | 01/11 | chưa có | — | — | góp ý và bảng tổng hợp đã soạn xong, chưa đăng lên PR |
| 6.4.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 01/11 | không đo được từ git | — | — | họp Chủ nhật, không có tệp nào trong git |
| 6.4.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 01/11 | không đo được từ git | — | — | biên bản chỉ có phần đo được từ git; nội dung họp chưa có |
| 7.1.1 | Test plan + ma trận phủ UC | Lead | 08/11 | chưa có | — | — | bản của Lead đã soạn xong, chưa đẩy lên nhánh |
| 7.1.2 | Test case backend | BE | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.1.3 | Test case frontend | FE | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.1.4 | Test case dữ liệu | DB | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.2.1 | Chuẩn chung + cấu hình lint | Lead | 08/11 | chưa có | — | — | bản của Lead đã soạn xong, chưa đẩy lên nhánh |
| 7.2.2 | Chuẩn code frontend | FE | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.2.3 | Chuẩn code backend | BE | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.2.4 | Chuẩn đặt tên bảng/migration | DB | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |
| 7.3.1 | Cập nhật WBS/Schedule/Risk theo thực tế 4 tuần đầu | Lead | 08/11 | chưa có | — | — | bản của Lead đã soạn xong, chưa đẩy lên nhánh |
| 7.3.2 | Review WBS chính thức | BE | 08/11 | chưa có | — | — | chờ đầu ra của Lead (7.1.1, 7.2.1, 7.3.1) và việc giao từ anh An |

## Tổng hợp
- 28 dòng WBS 5.1.1 đến 7.3.2: 16 chưa có; 8 PR mở; 2 có nhánh, chưa mở PR; 2 không đo được từ git.
