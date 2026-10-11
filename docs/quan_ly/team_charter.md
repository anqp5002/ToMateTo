# TEAM CHARTER — ToMateTo

> Owner: Lead | Reviewer: DB (và cả nhóm đọc) | Approver: Lead | Sprint: S0 (12–18/10/2026) | Bản: v2 — nhóm xác nhận ở buổi họp đầu rồi ký
> Đây là cam kết của nhóm về **cách làm việc**. Mục "đề xuất" là điểm xuất phát, nhóm sửa trực tiếp khi họp.

## 1. Mục đích và phạm vi nhóm

Nhóm 4 người thực hiện dự án ToMateTo — ứng dụng cộng đồng chia sẻ món ăn và quán ngon — từ phân tích yêu cầu, thiết kế đến cài đặt. Hai kết quả:

1. **Một sản phẩm chạy được** (ứng dụng Flutter + backend + cơ sở dữ liệu).
2. **Một repo `ToMateTo` thể hiện đúng quá trình**: thiết kế trước, code sau; từng phần theo sprint; có phân công, review chéo và lịch sử Pull Request của từng người.

Điều được chấm là nhóm **hiểu và tự làm được**, không chỉ có sản phẩm.

## 2. Vai trò và trách nhiệm

| Vai trò | Họ tên | Trách nhiệm xuyên suốt | Quyết định | Được review bởi |
|---|---|---|---|---|
| **Lead** | | Điều phối sprint, giữ kế hoạch/WBS, viết tài liệu quản lý, giữ chất lượng repo, **điều hành buổi họp Chủ nhật**, ký DOC, merge cuối | Khi tranh chấp xuyên vùng; phạm vi từng sprint | Cả nhóm |
| **FE** | | Phần giao diện: persona/stakeholder, wireframe, hi-fi UI, cài đặt ứng dụng Flutter | Mọi thứ thuộc giao diện | BE (hợp đồng API), Lead |
| **BE** | | Phần máy chủ: system context, process flow, FR, API, kiến trúc, thuật toán, cài đặt API/dịch vụ/trợ lý AI | Mọi thứ thuộc backend | FE (hợp đồng API), DB (truy vấn/schema), Lead |
| **DB** | | Phần dữ liệu: ERD, schema, data dictionary, DDL, migration, dữ liệu mẫu, Docker cho DB | Mọi thứ thuộc CSDL | BE (model↔service), Lead |

Ai làm DOC nào, ai review: theo WBS (`wbs_ban_dau.md`) và bảng phân công sprint — **reviewer được chỉ định theo từng sprint** (không cố định một người review suốt).

## 3. Nhịp làm việc tuần

Thời gian hạn chế nên **mỗi tuần chỉ họp trực tiếp một lần — vào Chủ nhật**. Phần còn lại làm việc bất đồng bộ.

**Trong tuần (T2–T7):**
1. Mỗi thành viên làm task của mình theo WBS, đẩy lên git qua nhánh/PR của mình.
2. Reviewer được chỉ định trong sprint đó **review chéo** phần của thành viên khác: đọc/kiểm thật, yêu cầu sửa khi sai; hai bên trao đổi trên PR đến khi đạt.
3. Phần nào không hiểu hoặc không thống nhất được → **ghi lại để hỏi vào buổi họp Chủ nhật**, không vòng vo chat.

**Buổi họp Chủ nhật (duy nhất trong tuần):**

| # | Phần | Nội dung |
|---|---|---|
| 1 | Báo cáo & trình bày | Từng thành viên trình bày phần mình làm trong tuần |
| 2 | Q&A | Thành viên đặt câu hỏi lẫn nhau để cùng hiểu; giải quyết các điểm review còn treo |
| 3 | Đánh giá & merge | Reviewer đánh giá lại → đạt → Lead merge vào `main` |
| 4 | Planning | Chốt task sprint/tuần kế tiếp theo WBS |

Biên bản họp 5–10 dòng: ngày, người dự, quyết định, việc giao.

## 4. Quy tắc làm tài liệu

1. **Thiết kế là của nhóm.** Mỗi DOC do nhóm tự viết theo mẫu manual tương ứng.
2. **Mọi khẳng định có nguồn:** dữ liệu thu thập từ internet/mạng xã hội, số đo, tài liệu hoặc chỉ rõ là giả thuyết. Không số liệu không nguồn; lời mơ hồ ("nhanh", "tốt") chỉ dùng kèm số đo.
3. **Header mỗi DOC:** Owner / Reviewer / Approver / Sprint / ngày.
4. Chỗ chưa biết ghi rõ "Giả thuyết" hoặc "Cần quyết" kèm ai quyết, khi nào.
5. Reviewer phải hỏi ít nhất 2 câu "tại sao" về phần mình đọc.
6. DOC cũng đi qua PR lên repo như code.

## 5. Quy tắc git

- **Không commit thẳng vào `main`.** Mỗi thay đổi một nhánh + Pull Request.
- Tên nhánh: `feat|fix|docs|chore/<scope>-<mô-tả>`, scope ∈ `fe` `be` `db` `infra` `docs`.
- Commit: `<type>(<scope>): <mô tả>`; body ghi `Sprint: Sx`, `DOC/WBS: <mã>`.
- **Mỗi PR có ít nhất 1 reviewer khác vai trò**; merge vào `main` diễn ra sau khi đạt — chốt tại buổi họp Chủ nhật.
- PR nhỏ (~≤400 dòng đổi, trừ tài liệu); mỗi sprint nhiều PR, không dồn cuối tuần.
- **Mỗi người commit bằng tài khoản của chính mình**, đúng việc mình làm.
- **Cấm đưa lên repo:** `.env` thật, khóa/mật khẩu (cả trong file `.md`), `uploads/`, `node_modules/`, `.venv/`, `build/`, `.dart_tool/`, log. Quét secret trước mỗi PR.
- Không force-push, không viết lại lịch sử `main`.
- Tag `sN-done` khi đóng sprint; `v1.0` ở cuối.

## 6. Quy trình lỗi

- Mức S1–S4; S1 (mất dữ liệu, bảo mật, app chết) xử lý ngay, không đợi họp.
- Ai thấy lỗi ghi: `[S?][fe|be|db] tiêu đề` + bước tái hiện + bằng chứng, báo Lead.
- Tái hiện bằng yêu cầu thô (GraphQL/curl) trước khi kết luận lỗi phía khác.
- Trễ hạn hơn 1 ngày: báo Lead **trong ngày** kèm lý do và ngày đề xuất mới — không đợi đến Chủ nhật.

## 7. Định nghĩa "xong" (Definition of Done)

**Một DOC xong khi:** người làm viết xong, reviewer chéo đã đọc thật và hỏi "tại sao" đạt, đã được đánh giá lại tại buổi họp, Lead ký và merge.

**Một lát code xong khi:** DOC thiết kế nó dựa vào đã được duyệt; test/build của lát chạy xanh; người làm **qua viva**; PR có reviewer duyệt; merge vào `main` tại buổi họp.

**Một sprint xong khi:** mọi DOC/lát code của sprint đã đạt, có biên bản buổi họp, đã gắn tag `sN-done`.

## 8. Tiêu chí "hiểu thật" (viva)

Trước khi lát code merge, người làm qua 3 cửa (kiểm tại buổi họp Chủ nhật):

1. **Trình bày bằng lời** luồng của phần mình: một thao tác của người dùng đi qua những hàm/file nào, dữ liệu đổi ra sao.
2. **Demo chạy** (FE: chạy màn; BE: gọi API thật; DB: migration lên/xuống + xem bảng).
3. **Trả lời 3–5 câu hỏi** của Lead và reviewer về thuật toán, quyết định thiết kế, lỗi có thể gặp và cách xử lý.

Chưa đạt: học lại và viva lại, PR chưa merge.

## 9. Xử lý xung đột và trễ hạn

- Tranh chấp trong vùng của ai, người đó quyết; xuyên vùng thì Lead quyết; bế tắc thì đưa vào buổi họp biểu quyết.
- Người review và người làm bất đồng: thử bằng thí nghiệm hoặc đọc nguồn, không tranh luận theo ý kiến.
- Trễ hạn: báo trong ngày; Lead cắt phạm vi theo thứ tự ưu tiên ở Vision mục 4.1, **không kéo dài hạn cuối**.
- Vắng đột xuất: báo Lead trước; nhóm chia lại việc rõ ràng.

## 10. Chữ ký

| Vai trò | Họ tên | Ngày ký | Chữ ký |
|---|---|---|---|
| Lead | | | |
| FE | | | |
| BE | | | |
| DB | | | |
