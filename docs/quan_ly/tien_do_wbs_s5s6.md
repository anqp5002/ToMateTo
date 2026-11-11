# Tiến độ WBS S5 + S6 (tuần W3, hạn 01/11) — đo ngày 08/11/2026

Trạng thái: **chưa có** · **có nhánh, chưa mở PR** · **PR mở** · **đã merge**. Nhánh `main` dừng ở commit `393268f` (23/10, hết S2); chưa có DOC nào của S3–S6 vào `main`.

| WBS | Công việc | Vai | Hạn | Trạng thái | Nhánh @SHA | Commit cuối | Ghi chú |
|---|---|---|---|---|---|---|---|
| 5.1.1 | Class diagram backend (6.1-A) | BE | 01/11 | có nhánh, chưa mở PR | `docs/be-s5-class-design-pr` @2809832 | 07/11 | 2 commit; trễ 6 ngày so với hạn |
| 5.1.2 | Class/provider diagram frontend (6.1-A) | FE | 01/11 | PR #22 mở | `docs/fe-s5-class-sequence` @c3b8b46 | 01/11 | đúng hạn; đã có 1 bình luận review của BE (04/11) |
| 5.1.3 | Review class diagrams | Lead | 01/11 | chưa có | — | — | chưa có góp ý trên PR/issue |
| 5.2.1 | Sequence backend (6.2-A) | BE | 01/11 | có nhánh, chưa mở PR | `docs/be-s5-sequence-diagrams` @ed27b57 | 03/11 | trễ 2 ngày |
| 5.2.2 | Sequence frontend (6.2-A) | FE | 01/11 | PR #22 mở | `docs/fe-s5-class-sequence` @c3b8b46 | 01/11 | chung PR với 5.1.2 |
| 5.2.3 | Review sequence | Lead | 01/11 | chưa có | — | — | chưa có góp ý trên PR/issue |
| 5.3.1 | Data dictionary + DDL (6.4-A/B) | DB | 01/11 | có nhánh, chưa mở PR | `docs/db-s5-data-dictionary-ddl` @552c454 | 02/11 | trễ 1 ngày; nhánh mang theo 7 file của người khác (4.1-A, 4.2-C, 4.3-A, 4.3-B, 5.3-A, 5.3-B, 5.4-A) và `.gitignore` |
| 5.3.2 | Review DDL | BE | 01/11 | chưa có | — | — | chưa thấy bình luận nào của BE |
| 6.1.1 | Mockup hi-fi + design system (6.3-A/B) | FE | 01/11 | PR #23 mở | `docs/fe-s6-mockups-error-handling` @999e0be | 06/11 | trễ 5 ngày; 18 file SVG (MH-01…MH-19, không có MH-04) |
| 6.1.2 | Review UI | Lead | 01/11 | chưa có | — | — | chưa có góp ý trên PR/issue |
| 6.2.1 | Đặc tả thuật toán (7.1-A) | BE | 01/11 | chưa có | — | — | không nhánh nào chứa 7.1-A |
| 6.2.2 | Truy vấn/chỉ mục cho thuật toán | DB | 01/11 | chưa có | — | — | phụ thuộc 6.2.1 |
| 6.2.3 | Review thuật toán | Lead | 01/11 | chưa có | — | — | chờ 6.2.1; có sẵn bộ câu hỏi |
| 6.3.1 | Đặc tả xử lý lỗi backend (7.2-A BE) | BE | 01/11 | chưa có | — | — | không nhánh nào chứa phần BE |
| 6.3.2 | Đặc tả xử lý lỗi frontend (7.2-A FE) | FE | 01/11 | PR #23 mở | `docs/fe-s6-mockups-error-handling` @999e0be | 06/11 | chung PR với 6.1.1 |
| 6.3.3 | Tổng hợp + review 7.2-A | Lead | 01/11 | chưa có | — | — | chưa có góp ý trên PR; phần BE chờ 6.3.1 |
| 6.4.1 | Họp CN 01/11 | Cả nhóm | 01/11 | — | — | — | không đo được từ git |
| 6.4.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 01/11 | chưa có | — | — | biên bản chưa có; tiến độ WBS đã cập nhật theo thực tế ngày 08/11 ở bảng này |

## Tổng hợp
- 18 dòng WBS: 0 đã merge; 4 dòng PR mở (5.1.2, 5.2.2, 6.1.1, 6.3.2; thuộc 2 PR #22 và #23, đều của FE); 3 dòng có nhánh chưa mở PR (5.1.1, 5.2.1, 5.3.1); 10 dòng chưa có (5.1.3, 5.2.3, 5.3.2, 6.1.2, 6.2.1, 6.2.2, 6.2.3, 6.3.1, 6.3.3, 6.4.2); 1 dòng không đo được từ git (6.4.1).
- Phụ thuộc: 6.2.2 chờ 6.2.1; 6.2.3 chờ 6.2.1; 6.3.3 phần BE chờ 6.3.1; S9 (bài đăng/feed) cần S5 và 5.3.1 gộp được.
- Rủi ro gộp: nhánh DB 5.3.1 chứa bản cũ của tài liệu thuộc người khác; gộp nguyên nhánh sẽ ghi đè bản của chủ file.
