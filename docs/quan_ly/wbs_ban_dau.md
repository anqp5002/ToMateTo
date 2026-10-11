# WBS BAN ĐẦU (v0) — ToMateTo

> Owner: Lead | Reviewer: DB | Approver: Lead | Sprint: S0 (đóng CN 11/10/2026)
> Kế hoạch phía trước của nhóm cho toàn bộ dự án. Bản chính thức (DOC 7.5-A/B/C) viết lại ở S7 sau khi có số liệu thực tế.
> Mẫu: manual 7.5 Task 7.5.1 (cây công việc, ước lượng, vai trò, phụ thuộc).

## 1. Nguyên tắc lập kế hoạch

- **Nhịp làm việc:** 2 sprint mỗi tuần; mỗi tuần chỉ họp trực tiếp 1 lần vào Chủ nhật (theo `team_charter.md` mục 3). Trong tuần làm việc bất đồng bộ: thành viên làm task → đẩy PR → reviewer chéo review → đánh giá và merge tại buổi họp CN.
- **Thiết kế trước, code sau:** S0–S7 là phân tích và thiết kế; S8–S11 là cài đặt, tách thành các lát cài đặt bám theo đúng thiết kế đã duyệt (mục 2).
- **Reviewer xoay theo sprint** (không cố định một người), theo cột Vai trò của từng task review.
- **Rolling wave:** sprint gần (S0–S1) chia nhỏ tới ≤2 ngày công; sprint xa ở mức gói việc, chia lại vào đầu tuần.
- **Ước lượng = ngày công** (1 người × 1 ngày tập trung). Con số là đề xuất của người lập; nhóm xác nhận/sửa ở buổi họp.
- **Giả định năng lực:** ~4 ngày công/người/tuần (cần xác nhận). Ký hiệu: `~` sát trần, `⚠` vượt trần. S0 là tuần khởi động đã được làm trong vài ngày, tải cao hơn nhưng không áp trần.
- **Task "Cả nhóm"** (họp CN, workshop, ký duyệt): ước lượng ghi "x/người" — mỗi người tốn x ngày công, đã cộng vào tải từng vai trò.

## 2. Lịch tổng quan

| Tuần | Sprint | Nội dung | Buổi họp CN |
|---|---|---|---|
| W0 · 11/10 | S0 | Khởi động: Vision, Personas/Stakeholder, System Context, Charter, WBS | 11/10 |
| W1 · 12–18/10 | S1 + S2 | Yêu cầu: UC, Process, ERD khái niệm + FR, NFR, Wireframe, Ưu tiên | 18/10 |
| W2 · 19–25/10 | S3 + S4 | Kiến trúc + HLD chi tiết | 25/10 |
| W3 · 26/10–01/11 | S5 + S6 | LLD: Class, Sequence, DDL + UI hi-fi, Thuật toán, Lỗi | 01/11 |
| W4 · 02–08/11 | S7 + S8 | Test/Chuẩn/WBS chính thức + cài đặt nền tảng | 08/11 |
| W5 · 09–15/11 | S9 + S10 | Cài đặt lõi nội dung + tương tác & khám phá | 15/11 |
| W6 · 16–22/11 | S11 | Trợ lý AI + hoàn thiện + phát hành v1.0 + báo cáo | 22/11 |
| Dự phòng | — | 23/11 → 18/12: sửa lỗi, hoàn thiện, chuẩn bị thuyết trình | — |

**Phụ thuộc thiết kế → cài đặt:** S8 (nền tảng) cần S4 (HLD); S9 (bài đăng/feed) cần S5 (API, DB spec); S10 (tương tác/khám phá) cần S6; S11 (AI + phát hành) cần S7. Thiết kế đi trước đúng một tuần nên điều kiện luôn thỏa nếu đường găng không trễ.

## 3. Cây công việc theo sprint

### S0 · W0 · đóng CN 11/10 — Khởi động: Vision, Personas/Stakeholder, System Context, Charter, WBS

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **0.1** | **Quản lý & luật làm việc** | | | | |
| 0.1.1 | Chốt luật làm việc, cách review chéo, giờ họp CN | Lead | 0.5 | — | biên bản |
| 0.1.2 | Viết Team Charter | Lead | 0.5 | 0.1.1 | team_charter.md |
| 0.1.3 | Lập WBS v0 + rủi ro ban đầu | Lead | 1 | 0.1.1 | wbs_ban_dau.md |
| 0.1.4 | Review Charter + WBS | DB | 0.5 | 0.1.2, 0.1.3 | góp ý trên PR |
| 0.1.5 | Thiết lập repo ToMateTo: khung thư mục, quy tắc nhánh, mẫu PR | DB | 0.5 | 0.1.2 | repo sẵn sàng |
| **0.2** | **DOC 1.1-A Vision** | | | | |
| 0.2.1 | Thu thập nguồn trên internet + mạng xã hội (bài chia sẻ món ăn, hội nhóm review, ứng dụng cùng loại) | Lead | 0.5 | — | danh sách nguồn |
| 0.2.2 | Phân tích nguồn → pain points (kèm link nguồn) | FE | 0.75 | 0.2.1 | pain points |
| 0.2.3 | Viết Vision (6 mục theo manual 1.1) | Lead | 1.25 | 0.2.2 | 1.1_vision.md |
| 0.2.4 | Review Vision | BE | 0.5 | 0.2.3 | góp ý trên PR |
| **0.3** | **DOC 1.2-A/B Personas + Stakeholder** | | | | |
| 0.3.1 | Viết 2–3 persona từ phân tích internet/mạng xã hội | FE | 1.5 | 0.2.2 | persona |
| 0.3.2 | Lập Stakeholder Register | FE | 1 | 0.2.3 | stakeholder |
| 0.3.3 | Review Personas + Stakeholder | Lead | 0.5 | 0.3.1, 0.3.2 | góp ý + ký |
| **0.4** | **DOC 1.3-A System Context** | | | | |
| 0.4.1 | Vẽ System Context + mô tả hệ thống ngoài | BE | 1.5 | 0.2.3 | system context |
| 0.4.2 | Review System Context | DB | 0.5 | 0.4.1 | góp ý trên PR |
| **0.5** | **Họp Chủ nhật 11/10 (đóng S0)** | | | | |
| 0.5.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 0.5.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 0.5.1 | biên bản |

Tải sprint: Lead 4.75 · FE 3.5 · BE 2.25 · DB 1.75

### S1 · W1 · 12–18/10 — Yêu cầu (1): Use Case, Process Flow, Conceptual ERD

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **1.1** | **Phân tích nghiệp vụ (cơ sở mô hình hoá UC)** | | | | |
| 1.1.1 | Liệt kê màn hình & luồng người dùng cần có | FE | 0.5 | 0.2.2 | danh sách màn |
| 1.1.2 | Liệt kê thao tác hệ thống cần có | BE | 0.5 | 0.2.2 | danh sách thao tác |
| 1.1.3 | Liệt kê thực thể dữ liệu cần có | DB | 0.5 | 0.2.2 | danh sách thực thể |
| **1.2** | **DOC 2.1-A/B Use Case** | | | | |
| 1.2.1 | Workshop actor + danh sách UC (Lead dẫn) | Cả nhóm | 0.25/người | 1.1 | danh sách UC |
| 1.2.2 | UC spec: tài khoản, feed, bài đăng, hồ sơ | FE | 1.25 | 1.2.1 | UC spec |
| 1.2.3 | UC spec: tương tác, khám phá, trợ lý AI | BE | 1.25 | 1.2.1 | UC spec |
| 1.2.4 | Gộp Use Case Diagram, kiểm trùng/thiếu | Lead | 0.75 | 1.2.2, 1.2.3 | UC diagram |
| 1.2.5 | Review UC | DB | 0.5 | 1.2.4 | góp ý trên PR |
| **1.3** | **DOC 2.2-A Process Flow** | | | | |
| 1.3.1 | 4–5 luồng chính (đăng bài, thích + thông báo, theo dõi, báo cáo → ẩn bài, gợi ý AI) | BE | 1 | 1.2.4 | process flow |
| 1.3.2 | Review Process Flow | FE | 0.25 | 1.3.1 | góp ý trên PR |
| **1.4** | **DOC 2.3-A Conceptual ERD** | | | | |
| 1.4.1 | Thực thể + quan hệ khái niệm | DB | 1.5 | 1.2.4 | conceptual ERD |
| 1.4.2 | Review ERD | BE | 0.25 | 1.4.1 | góp ý trên PR |

Tải sprint: Lead 1 · FE 2.25 · BE 3.25 · DB 2.75

### S2 · W1 · 12–18/10 — Yêu cầu (2): FR, NFR, Wireframe, Ưu tiên + ký duyệt

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **2.1** | **DOC 3.1-A Functional Requirements** | | | | |
| 2.1.1 | Viết FR từ UC | BE | 1 | 1.2.4 | FR list |
| 2.1.2 | Bổ sung FR phía giao diện | FE | 0.25 | 2.1.1 | FR bổ sung |
| 2.1.3 | Review FR | Lead | 0.25 | 2.1.1 | góp ý trên PR |
| **2.2** | **DOC 3.2-A NFR** | | | | |
| 2.2.1 | Viết NFR có số đo mục tiêu | Lead | 0.75 | 0.2.3 | NFR |
| 2.2.2 | Review NFR phía dữ liệu | DB | 0.25 | 2.2.1 | góp ý trên PR |
| **2.3** | **DOC 3.3-A/B Wireframe + Navigation** | | | | |
| 2.3.1 | Wireframe các màn + sơ đồ điều hướng | FE | 1.5 | 1.2.4 | wireframe + nav |
| 2.3.2 | Review Wireframe | Lead | 0.25 | 2.3.1 | góp ý trên PR |
| **2.4** | **DOC 3.4-A/B/C Ưu tiên + ký duyệt yêu cầu** | | | | |
| 2.4.1 | Ma trận MoSCoW | Lead | 0.5 | 2.1.1 | MoSCoW |
| 2.4.2 | Review MoSCoW | BE | 0.25 | 2.4.1 | góp ý trên PR |
| 2.4.3 | Ký duyệt bộ yêu cầu tại buổi họp CN | Cả nhóm | 0.25/người | 2.1–2.3 | biên bản + ký |
| **2.5** | **Họp Chủ nhật 18/10** | | | | |
| 2.5.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 2.5.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 2.5.1 | biên bản |

Tải sprint: Lead 2.5 · FE 2.25 · BE 1.75 · DB 0.75

### S3 · W2 · 19–25/10 — Kiến trúc: Drivers, Tech Stack, Kiến trúc hệ thống + ADR

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **3.1** | **DOC 4.1-A Architecture Drivers** | | | | |
| 3.1.1 | Drivers từ NFR + ràng buộc | Lead | 0.75 | 2.2.1 | drivers |
| 3.1.2 | Review drivers | BE | 0.25 | 3.1.1 | góp ý trên PR |
| **3.2** | **DOC 4.2-A Technology Stack Decision** | | | | |
| 3.2.1 | Lựa chọn + phương án bị loại: backend | BE | 0.75 | 3.1.1 | decision BE |
| 3.2.2 | Lựa chọn + phương án bị loại: frontend | FE | 0.75 | 3.1.1 | decision FE |
| 3.2.3 | Lựa chọn + phương án bị loại: cơ sở dữ liệu | DB | 0.5 | 3.1.1 | decision DB |
| 3.2.4 | Review tech stack | Lead | 0.25 | 3.2.1–3 | góp ý trên PR |
| **3.3** | **DOC 4.3-A/B System Architecture + ADR** | | | | |
| 3.3.1 | Vẽ kiến trúc hệ thống | Lead | 0.75 | 3.2.4 | architecture |
| 3.3.2 | Review kiến trúc | DB | 0.25 | 3.3.1 | góp ý trên PR |
| 3.3.3a | ADR phần quản lý/hạ tầng | Lead | 0.25 | 3.3.1 | ADR |
| 3.3.3b | ADR phần backend | BE | 0.5 | 3.3.1 | ADR |
| 3.3.3c | ADR phần frontend | FE | 0.5 | 3.3.1 | ADR |
| 3.3.3d | ADR phần dữ liệu | DB | 0.25 | 3.3.1 | ADR |

Tải sprint: Lead 2 · FE 1.25 · BE 1.5 · DB 1

### S4 · W2 · 19–25/10 — HLD chi tiết: Component, API, DB vật lý, Bảo mật + duyệt HLD

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **4.1** | **DOC 5.1-A/B Component + Responsibility** | | | | |
| 4.1.1 | Component + matrix: backend | BE | 0.5 | 3.3.1 | component BE |
| 4.1.2 | Component + matrix: frontend | FE | 0.75 | 3.3.1 | component FE |
| 4.1.3 | Review component | Lead | 0.25 | 4.1.1, 4.1.2 | góp ý trên PR |
| **4.2** | **DOC 5.2-A API Specification** | | | | |
| 4.2.1 | Đặc tả API theo UC/FR | BE | 1 | 2.1.1 | API spec |
| 4.2.2 | Review API | FE | 0.25 | 4.2.1 | góp ý trên PR |
| **4.3** | **DOC 5.3-A/B Physical ERD + Schema** | | | | |
| 4.3.1 | Physical ERD + schema spec | DB | 1.5 | 1.4.1, 4.2.1 | physical ERD |
| 4.3.2 | Review schema | BE | 0.25 | 4.3.1 | góp ý trên PR |
| **4.4** | **DOC 5.4-A Security Design** | | | | |
| 4.4.1 | Thiết kế bảo mật (xác thực, phân quyền, lưu khóa) | BE | 0.5 | 3.3.1 | security |
| 4.4.2 | Review security | Lead | 0.25 | 4.4.1 | góp ý trên PR |
| **4.5** | **DOC 5.5-A/B Duyệt HLD** | | | | |
| 4.5.1 | Duyệt + ký HLD tại buổi họp CN | Cả nhóm | 0.25/người | 4.1–4.4 | biên bản + ký |
| **4.6** | **Họp Chủ nhật 25/10** | | | | |
| 4.6.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 4.6.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 4.6.1 | biên bản |

Tải sprint: Lead 1.25 · FE 1.5 · BE 2.75 · DB 2

### S5 · W3 · 26/10–01/11 — LLD 1/2: Class, Sequence, Data Dictionary + DDL

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **5.1** | **DOC 6.1-A Class Diagrams** | | | | |
| 5.1.1 | Class diagram backend | BE | 1 | 4.1.1, 4.2.1 | class BE |
| 5.1.2 | Class/provider diagram frontend | FE | 0.75 | 4.1.2 | class FE |
| 5.1.3 | Review class diagrams | Lead | 0.25 | 5.1.1, 5.1.2 | góp ý trên PR |
| **5.2** | **DOC 6.2-A Sequence Diagrams (≥10)** | | | | |
| 5.2.1 | Sequence luồng phía backend | BE | 0.75 | 5.1.1 | sequence BE |
| 5.2.2 | Sequence luồng phía frontend | FE | 0.75 | 5.1.2 | sequence FE |
| 5.2.3 | Review sequence | Lead | 0.25 | 5.2.1, 5.2.2 | góp ý trên PR |
| **5.3** | **DOC 6.4-A/B Data Dictionary + DDL** | | | | |
| 5.3.1 | Data dictionary + DDL | DB | 1.5 | 4.3.1 | dict + DDL |
| 5.3.2 | Review DDL | BE | 0.25 | 5.3.1 | góp ý trên PR |

Tải sprint: Lead 0.5 · FE 1.5 · BE 2 · DB 1.5

### S6 · W3 · 26/10–01/11 — LLD 2/2: UI hi-fi, Thuật toán, Xử lý lỗi

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **6.1** | **DOC 6.3-A/B UI Hi-fi + Design System** | | | | |
| 6.1.1 | Mockup hi-fi + design system | FE | 1.25 | 2.3.1 | hi-fi + DS |
| 6.1.2 | Review UI | Lead | 0.25 | 6.1.1 | góp ý trên PR |
| **6.2** | **DOC 7.1-A Algorithm Specifications** | | | | |
| 6.2.1 | Đặc tả thuật toán (phân trang feed, xu hướng, gần đây, quay món, gợi ý AI) | BE | 0.75 | 5.2.1 | algo spec |
| 6.2.2 | Phần truy vấn/chỉ mục dữ liệu cho các thuật toán | DB | 0.5 | 6.2.1 | bổ sung |
| 6.2.3 | Review thuật toán | Lead | 0.25 | 6.2.1 | góp ý trên PR |
| **6.3** | **DOC 7.2-A Error Handling** | | | | |
| 6.3.1 | Đặc tả xử lý lỗi backend | BE | 0.5 | 5.2.1 | error spec BE |
| 6.3.2 | Đặc tả xử lý lỗi frontend | FE | 0.25 | 5.2.2 | error spec FE |
| 6.3.3 | Tổng hợp + review | Lead | 0.25 | 6.3.1, 6.3.2 | error spec |
| **6.4** | **Họp Chủ nhật 01/11** | | | | |
| 6.4.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 6.4.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 6.4.1 | biên bản |

Tải sprint: Lead 1.25 · FE 1.75 · BE 1.5 · DB 0.75

### S7 · W4 · 02–08/11 — Kiểm thử, Chuẩn code, Kế hoạch triển khai chính thức

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **7.1** | **DOC 7.3-A/B/C Testing** | | | | |
| 7.1.1 | Test plan + ma trận phủ UC | Lead | 0.75 | 6.2.1 | test plan |
| 7.1.2 | Test case backend | BE | 0.5 | 7.1.1 | case BE |
| 7.1.3 | Test case frontend | FE | 0.5 | 7.1.1 | case FE |
| 7.1.4 | Test case dữ liệu | DB | 0.25 | 7.1.1 | case DB |
| **7.2** | **DOC 7.4-A/B Coding Standards** | | | | |
| 7.2.1 | Chuẩn chung + cấu hình lint | Lead | 0.25 | — | standards |
| 7.2.2 | Chuẩn code frontend | FE | 0.25 | 7.2.1 | FE standard |
| 7.2.3 | Chuẩn code backend | BE | 0.25 | 7.2.1 | BE standard |
| 7.2.4 | Chuẩn đặt tên bảng/migration | DB | 0.25 | 7.2.1 | DB standard |
| **7.3** | **DOC 7.5-A/B/C WBS + Schedule + Risk (bản chính thức)** | | | | |
| 7.3.1 | Cập nhật WBS/Schedule/Risk theo thực tế 4 tuần đầu | Lead | 0.75 | WBS v0 | WBS chính thức |
| 7.3.2 | Review WBS chính thức | BE | 0.25 | 7.3.1 | góp ý trên PR |

Tải sprint: Lead 1.75 · FE 0.75 · BE 1 · DB 0.5

### S8 · W4 · 02–08/11 — Cài đặt nền tảng: khung hệ thống, xác thực, dữ liệu lõi

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **8.1** | **Hạ tầng** | | | | |
| 8.1.1 | Cấu trúc repo, Docker Compose (backend + PostgreSQL), file cấu hình mẫu | Lead | 0.75 | 4.5.1 | stack chạy local |
| 8.1.2 | CI cơ bản: lint + test tự động trên PR | Lead | 0.5 | 8.1.1 | CI xanh |
| **8.2** | **Dữ liệu lõi** | | | | |
| 8.2.1 | Model + migration đầu: người dùng, món, quán | DB | 1 | 5.3.1 | migration chạy được |
| 8.2.2 | Dữ liệu mẫu ban đầu | DB | 0.5 | 8.2.1 | seed |
| 8.2.3 | Test migration lên/xuống | DB | 0.25 | 8.2.1 | test xanh |
| **8.3** | **Backend nền** | | | | |
| 8.3.1 | Khung API + GraphQL, cấu hình, xử lý lỗi chung | BE | 0.75 | 5.1.1, 6.3.1 | API khởi động |
| 8.3.2 | Đăng ký / đăng nhập / JWT / đặt lại mật khẩu | BE | 0.75 | 8.3.1, 8.2.1, 4.4.1 | API auth |
| 8.3.3 | Test API xác thực | BE | 0.5 | 8.3.2 | test xanh |
| **8.4** | **Frontend nền** | | | | |
| 8.4.1 | Khung Flutter: theme, router, client GraphQL, lưu phiên đăng nhập | FE | 1 | 5.1.2, 6.1.1 | app khởi động |
| 8.4.2 | Màn đăng nhập / đăng ký nối API thật | FE | 0.5 | 8.4.1, 8.3.2 | luồng auth chạy |
| 8.4.3 | Widget test màn auth | FE | 0.25 | 8.4.2 | test xanh |
| **8.5** | **Họp Chủ nhật 08/11 (viva lát S8)** | | | | |
| 8.5.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 8.5.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 8.5.1 | biên bản |

Tải sprint: Lead 1.75 · FE 2 · BE 2.25 · DB 2

### S9 · W5 · 09–15/11 — Cài đặt lõi nội dung: bài đăng, feed, tải ảnh

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **9.1** | **Dữ liệu** | | | | |
| 9.1.1 | Bảng bài đăng, ảnh, báo cáo + chỉ mục cho phân trang feed | DB | 0.75 | 8.2.1 | migration |
| 9.1.2 | Test truy vấn feed trên dữ liệu mẫu | DB | 0.25 | 9.1.1 | test xanh |
| **9.2** | **Backend** | | | | |
| 9.2.1 | API tạo/sửa/xoá bài, tải ảnh | BE | 0.75 | 9.1.1 | API post |
| 9.2.2 | API feed phân trang + chi tiết bài + báo cáo tự ẩn bài | BE | 0.75 | 9.2.1, 6.2.1 | API feed |
| 9.2.3 | Test API bài đăng/feed | BE | 0.5 | 9.2.2 | test xanh |
| **9.3** | **Frontend** | | | | |
| 9.3.1 | Màn feed + thẻ bài + chi tiết bài | FE | 0.75 | 9.2.2 | màn feed |
| 9.3.2 | Màn đăng bài (ảnh, món, quán, giá, vị trí) | FE | 0.75 | 9.2.1 | màn compose |
| 9.3.3 | Widget test feed/compose | FE | 0.25 | 9.3.2 | test xanh |
| **9.4** | **Tích hợp** | | | | |
| 9.4.1 | Kiểm thử tích hợp luồng đăng bài → feed | Lead | 0.5 | 9.2–9.3 | biên bản test |

Tải sprint: Lead 0.5 · FE 1.75 · BE 2 · DB 1

### S10 · W5 · 09–15/11 — Cài đặt tương tác & khám phá: thích, lưu, theo dõi, thông báo, bản đồ, quay món

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **10.1** | **Dữ liệu** | | | | |
| 10.1.1 | Bảng thích, bộ sưu tập, theo dõi, thông báo | DB | 0.75 | 9.1.1 | migration |
| 10.1.2 | Truy vấn quán gần theo vị trí + dữ liệu mẫu có toạ độ | DB | 0.5 | 6.2.2 | truy vấn + seed |
| **10.2** | **Backend** | | | | |
| 10.2.1 | API thích, lưu, theo dõi, thông báo | BE | 0.75 | 10.1.1 | API social |
| 10.2.2 | API xu hướng, quán gần, quay món, tìm kiếm | BE | 0.75 | 10.1.2, 6.2.1 | API discovery |
| 10.2.3 | Test API tương tác/khám phá | BE | 0.5 | 10.2.2 | test xanh |
| **10.3** | **Frontend** | | | | |
| 10.3.1 | Hồ sơ, bộ sưu tập, thông báo, nút thích/lưu/theo dõi | FE | 0.75 | 10.2.1 | màn social |
| 10.3.2 | Bản đồ quán gần, quay món, khám phá/tìm kiếm | FE | 0.75 | 10.2.2 | màn discovery |
| 10.3.3 | Widget test các màn mới | FE | 0.25 | 10.3.2 | test xanh |
| **10.4** | **Tích hợp** | | | | |
| 10.4.1 | Kiểm thử tích hợp luồng thích → thông báo, quán gần | Lead | 0.5 | 10.2–10.3 | biên bản test |
| **10.5** | **Họp Chủ nhật 15/11 (viva lát S9 + S10)** | | | | |
| 10.5.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 10.5.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 10.5.1 | biên bản |

Tải sprint: Lead 1 · FE 2 · BE 2.25 · DB 1.5

### S11 · W6 · 16–22/11 — Cài đặt trợ lý AI, hoàn thiện, phát hành v1.0 + báo cáo

| WBS | Công việc | Vai trò | Ước lượng (ngày công) | Phụ thuộc | Output |
|---|---|---|---|---|---|
| **11.1** | **Trợ lý AI** | | | | |
| 11.1.1 | Bảng phiên chat + tin nhắn + bản nháp bài | DB | 0.5 | 10.1.1 | migration |
| 11.1.2 | Dịch vụ trợ lý: phân loại ý định, gợi ý từ dữ liệu, soạn bài nháp, chế độ lùi khi AI lỗi | BE | 1 | 11.1.1, 6.2.1, 6.3.1 | API chat |
| 11.1.3 | Test dịch vụ trợ lý (bộ 20 câu hỏi thử của Vision O4) | BE | 0.5 | 11.1.2 | kết quả O4 |
| 11.1.4 | Màn chat + chuyển bản nháp sang màn đăng bài | FE | 0.75 | 11.1.2 | màn chat |
| 11.1.5 | Widget test màn chat | FE | 0.25 | 11.1.4 | test xanh |
| **11.2** | **Hoàn thiện & phát hành** | | | | |
| 11.2.1 | Dữ liệu mẫu đủ demo (≥200 bài) + kiểm tra hiệu năng O2 | DB | 0.75 | 10.1.2 | seed + số đo |
| 11.2.2 | Chạy kịch bản kiểm thử O1–O5, ghi kết quả | Lead | 0.5 | 11.1, 11.2.1 | báo cáo test |
| 11.2.3 | Hoàn thiện CI, tag v1.0, hướng dẫn chạy | Lead | 0.5 | 11.2.2 | v1.0 |
| **11.3** | **Báo cáo + trình bày** | | | | |
| 11.3.1 | Báo cáo tổng kết dự án | Lead | 0.75 | 11.2.2 | báo cáo |
| 11.3.2a | Chuẩn bị trình bày module FE | FE | 0.25 | 11.3.1 | slide FE |
| 11.3.2b | Chuẩn bị trình bày module BE | BE | 0.25 | 11.3.1 | slide BE |
| 11.3.2c | Chuẩn bị trình bày module DB | DB | 0.25 | 11.3.1 | slide DB |
| **11.4** | **Họp Chủ nhật 22/11 (viva S11 + release review)** | | | | |
| 11.4.1 | Họp CN: trình bày, Q&A, reviewer đánh giá lại, merge vào main, chốt task tuần sau | Cả nhóm | 0.25/người | các task trong tuần | PR đã merge |
| 11.4.2 | Biên bản họp + cập nhật tiến độ WBS | Lead | 0.25 | 11.4.1 | biên bản |

Tải sprint: Lead 2.25 · FE 1.5 · BE 2 · DB 1.75

## 4. Kiểm tải theo vai trò (ngày công)

### 4.1 Tải theo sprint

| Sprint | Tuần | Lead | FE | BE | DB |
|---|---|---|---|---|---|
| S0 | W0 · đóng CN 11/10 | 4.75 | 3.5 | 2.25 | 1.75 |
| S1 | W1 · 12–18/10 | 1 | 2.25 | 3.25 | 2.75 |
| S2 | W1 · 12–18/10 | 2.5 | 2.25 | 1.75 | 0.75 |
| S3 | W2 · 19–25/10 | 2 | 1.25 | 1.5 | 1 |
| S4 | W2 · 19–25/10 | 1.25 | 1.5 | 2.75 | 2 |
| S5 | W3 · 26/10–01/11 | 0.5 | 1.5 | 2 | 1.5 |
| S6 | W3 · 26/10–01/11 | 1.25 | 1.75 | 1.5 | 0.75 |
| S7 | W4 · 02–08/11 | 1.75 | 0.75 | 1 | 0.5 |
| S8 | W4 · 02–08/11 | 1.75 | 2 | 2.25 | 2 |
| S9 | W5 · 09–15/11 | 0.5 | 1.75 | 2 | 1 |
| S10 | W5 · 09–15/11 | 1 | 2 | 2.25 | 1.5 |
| S11 | W6 · 16–22/11 | 2.25 | 1.5 | 2 | 1.75 |
| **Tổng** | | **20.5** | **22** | **24.5** | **17.25** |

### 4.2 Tải thực theo tuần (cộng các sprint cùng tuần)

| Tuần | Thời gian | Sprint | Lead | FE | BE | DB |
|---|---|---|---|---|---|---|
| W0 | đóng CN 11/10 | S0 | 4.75 | 3.5 | 2.25 | 1.75 |
| W1 | 12–18/10 | S1 + S2 | 3.5 | 4.5 ⚠ | 5 ⚠ | 3.5 |
| W2 | 19–25/10 | S3 + S4 | 3.25 | 2.75 | 4.25 ~ | 3 |
| W3 | 26/10–01/11 | S5 + S6 | 1.75 | 3.25 | 3.5 | 2.25 |
| W4 | 02–08/11 | S7 + S8 | 3.5 | 2.75 | 3.25 | 2.5 |
| W5 | 09–15/11 | S9 + S10 | 1.5 | 3.75 ~ | 4.25 ~ | 2.5 |
| W6 | 16–22/11 | S11 | 2.25 | 1.5 | 2 | 1.75 |

**Kết luận:** với giả định 4 ngày công/người/tuần, các tuần W2–W6 nằm trong ngưỡng. W1 nặng nhất (BE 5 ⚠, FE 4.5 ⚠) — buổi họp CN 11/10 phải xác nhận năng lực thật; nếu thấp hơn giả định thì san một phần S2 sang W2. S0 không áp trần vì là tuần khởi động đã được thực hiện trước.

### 4.3 Nhận xét
- **DB nhẹ hơn hẳn** (17,25 vs ~22): đề xuất nhận thêm viết dữ liệu mẫu cho demo và tối ưu truy vấn ở các sprint sau.
- **Lead** phải dành thời lượng chấm viva và merge ở mỗi buổi họp CN (đã cộng trong task họp).
- Số liệu là ước lượng; nhóm hiệu chỉnh từng tuần và cập nhật WBS.

## 5. Đường găng

```
Vision → Persona/UC → FR + Wireframe → NFR/Drivers → Tech stack → Kiến trúc
→ API + DB vật lý → Class + Sequence + DDL → Thuật toán → Test plan/WBS chính thức
→ code S8 → S9 → S10 → S11 → v1.0
```
Trễ một DOC trên đường găng đẩy lát cài đặt tương ứng. Vì chỉ họp 1 lần/tuần: reviewer phản hồi ≤24 giờ trong tuần, trễ hạn phải báo Lead trong ngày — không đợi đến buổi họp.

## 6. Rủi ro ban đầu (v0)

| # | Rủi ro | Khả năng | Ảnh hưởng | Phòng ngừa | Người theo dõi |
|---|---|---|---|---|---|
| R1 | W1 quá tải (BE 5, FE 4.5 ngày công) | Cao | Trung bình | Xác nhận năng lực tại họp CN 11/10; san S2 sang W2 nếu cần | Lead |
| R2 | Chỉ 1 buổi họp/tuần → vấn đề bị treo cả tuần | Trung bình | Cao | Quy tắc "báo kẹt trong ngày"; reviewer phản hồi ≤24h | Lead |
| R3 | Thành viên push code chưa hiểu rõ | Trung bình | Cao | Viva tại buổi họp trước khi merge; chưa đạt thì merge tuần sau | Lead |
| R4 | Tài liệu viết qua loa hoặc lấy ý tưởng ngoài không hiểu | Trung bình | Trung bình | Reviewer hỏi "tại sao" ≥2 câu/DOC; sửa đến khi giải thích được | Reviewer |
| R5 | Trễ DOC đường găng đẩy lát code | Trung bình | Cao | Lead theo đường găng; san lịch ngay khi thấy trễ | Lead |
| R6 | Lộ khóa/mật khẩu lên repo | Thấp | Rất cao | `.gitignore` + quét secret trước PR (cả file `.md`) | Mọi người |
| R7 | Nhà cung cấp AI miễn phí không ổn định | Cao | Trung bình | Thiết kế lỗi có chế độ lùi (DOC 7.2); test trợ lý chạy không-AI | BE |
| R8 | Lead là nút cổ chai review/viva | Trung bình | Trung bình | Reviewer chéo lọc trước; Lead chỉ hỏi sâu | Lead |

## 7. Điều cần nhóm quyết tại buổi họp CN 11/10

1. Năng lực thật mỗi người mỗi tuần → xử lý W1 quá tải (mục 4.2).
2. Thứ tự reviewer chéo của từng sprint (xoay, không cố định).
3. Giờ họp Chủ nhật cố định hằng tuần.
4. Điền tên bốn vai trò vào Charter và bảng ký các file S0.

## 8. Chữ ký

| Vai trò | Họ tên | Ngày | Chữ ký |
|---|---|---|---|
| Lead (approve) | | | |
| DB (reviewer) | | | |
