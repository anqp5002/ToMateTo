# Góp ý 7.1-A Đặc tả thuật toán backend và 7.2-A Đặc tả xử lý lỗi backend

## 7.1-A BE

### Nội dung

- [ ] 1. 7.1-A_algorithm_specifications_backend.md:81@23a5f14 — tiêu đề mục 3 ghi Tính và đọc xu hướng nhưng giả mã chỉ mô tả job tính định kỳ, thiếu toàn bộ giải thuật truy vấn đọc trending của người dùng (5.2-A mục 4.2 dòng 131)
- [ ] 2. 7.1-A_algorithm_specifications_backend.md:129@23a5f14 — bước chọn ngẫu nhiên không nêu phân phối xác suất và không nêu cách sinh số ngẫu nhiên hay hạt giống để kiểm thử lặp lại được (7.1-A BE mục 5; 3.2-A NFR-14)
- [ ] 3. 7.1-A_algorithm_specifications_backend.md:130@23a5f14 — trả món được chọn cùng lý do gợi ý nhưng thiếu toàn bộ quy tắc sinh giá trị cho trường reason trong DishSuggestion (5.2-A mục 4.1 dòng 640)
- [ ] 4. 7.1-A_algorithm_specifications_backend.md:142@23a5f14 — bước lấy ngữ cảnh gửi AI không nêu số tin nhắn lịch sử và giới hạn token vào và ra (7.1-A BE mục 6; 3.2-A NFR-13 dòng 91)
- [ ] 5. 7.1-A_algorithm_specifications_backend.md:151@23a5f14 — thiếu giải thuật và bước kiểm tra để trích xuất AssistantDraft và post_draft UC-19 từ phản hồi của mô hình AI (5.2-A mục 4.1 dòng 624 và 5.3-B mục T19 dòng 208)
- [ ] 6. 7.1-A_algorithm_specifications_backend.md:180@23a5f14 — sắp xếp kết quả tìm kiếm theo mức phù hợp và id không đảm bảo duy nhất khi tìm đa thực thể vì món quán và bài có dải id độc lập (5.2-A mục 4.1-4.2 dòng 130, 609)

### Nhất quán

- [ ] 7. 7.1-A_algorithm_specifications_backend.md:41@23a5f14 — đầu ra feed khai báo thiếu cấu trúc Relay Connection edges chứa cursor từng bài, chỉ nêu danh sách bài, endCursor và hasNextPage (5.2-A mục 4.1-4.2 dòng 118, 124)
- [ ] 8. 7.1-A_algorithm_specifications_backend.md:52@23a5f14 — khoá sắp xếp trending khai báo cột id nhưng bảng snapshot T21 trending_post_snapshots không có cột id mà dùng post_id (5.3-B mục T21 dòng 236)
- [ ] 9. 7.1-A_algorithm_specifications_backend.md:66@23a5f14 — payload cursor cho TRENDING khai báo chứa runId, score và id, dùng sai tên cột id thay vì post_id của bảng T21 (5.3-B mục T21 và mục con trỏ dòng 236, 308)
- [ ] 10. 7.1-A_algorithm_specifications_backend.md:83@23a5f14 — đầu ra job xu hướng chỉ ghi run cùng snapshot bài và món, thiếu nhóm snapshot thẻ T23 trending_tag_snapshots (5.3-B mục T23 dòng 244-248 và 5.1-AB mục 9 dòng 569)
- [ ] 11. 7.1-A_algorithm_specifications_backend.md:97@23a5f14 — lượt lưu trong cửa sổ nêu tính theo thời điểm tạo nhưng bảng T15 collection_items dùng cột added_at chứ không có created_at (5.3-B mục T15 dòng 174, 180)

## 7.2-A BE

### Hình thức

- [ ] 12. 7.2-A_error_handling_backend.md:103@23a5f14 — dòng này ghi một câu tiếng Việt ở cột HTTP Status thay cho mã số, không theo khuôn của cả bảng và không đối chiếu được với bảng mã HTTP của upload (5.2-A mục 5.2 dòng 331-338; 7.2-A BE mục 4 dòng 117)
- [ ] 13. 7.2-A_error_handling_backend.md:166@23a5f14 — mục 9 mở đầu bằng "Mã E dưới đây giữ theo đặc tả FE chi tiết" và dùng ký hiệu E1 đến E4, nhưng 2.1-B và 7.2-A FE không định nghĩa mã E nào, nên ký hiệu không truy được (2.1-B mục 4; 7.2-A FE)

### Nội dung

- [ ] 14. 7.2-A_error_handling_backend.md:146@23a5f14 — mục 6 liệt kê trường log theo ba mức nhưng không có trường định danh người dùng; câu "Định danh người dùng chỉ dùng khi cần" không nêu quy tắc che, trong khi 5.4-A quy định che email (5.4-A mục 4.4 dòng 272-282)
- [ ] 15. 7.2-A_error_handling_backend.md:146@23a5f14 — mục 6 thiếu hai trong bốn sự kiện log bắt buộc của NFR-09: cấp mã đặt lại mật khẩu và thất bại gửi thông báo đẩy (3.2-A NFR-09 dòng 59)
- [ ] 16. 7.2-A_error_handling_backend.md:152@23a5f14 — mục 7 nói createPost, register, askAssistant không tự gửi lại khi mất phản hồi nhưng không nhắc khoá chống tạo trùng; 5.2-A nêu header Idempotency-Key và ghi đang chờ chốt (5.2-A mục 12.10 dòng 859)
- [ ] 17. 7.2-A_error_handling_backend.md:154@23a5f14 — mục 7 nói xoá ảnh khỏi nơi lưu có thể được thử lại qua job bền vững nhưng không nêu xử lý ảnh mồ côi sau khi giao dịch tạo bài bị hoàn tác; 5.1-A/B khai job dọn ảnh mồ côi chạy hằng ngày cho tình huống này (5.1-AB mục 2.4 dòng 570)
- [ ] 18. 7.2-A_error_handling_backend.md:157@23a5f14 — ngắt mạch mở sau 5 lỗi liên tiếp và half-open sau 30 giây, nhưng 6.2-A BE và 5.1-A/B không có cơ chế ngắt mạch nào nên hai con số không có nơi đối chiếu (5.1-AB mục 2.3 và mục 2.4; 6.2-A BE)
- [ ] 19. 7.2-A_error_handling_backend.md:182@23a5f14 — mục 9 chỉ ánh xạ luồng ngoại lệ của 15 UC, thiếu UC-14, UC-15, UC-17, UC-19, UC-20; riêng UC-15 có mã RATE_LIMITED (vượt 10 báo cáo mỗi giờ) ở 5.2-A mà 7.2-A BE không nhắc (2.1-B mục 4 dòng 81-82; 5.2-A mục 12.5 dòng 742)

### Nhất quán

- [ ] 20. 7.2-A_error_handling_backend.md:66@23a5f14 — bảng mã sang nhóm ngoại lệ ở dòng 64-69 xếp NOT_AVAILABLE vào NotFoundError, nhưng dòng 97 trong cùng tệp mô tả NOT_AVAILABLE là "Tài nguyên không khả dụng với người xem" tức lỗi quyền xem; hai cách phân nhóm trong cùng một tài liệu cho cùng một mã (5.2-A mục 6 dòng 368: NOT_AVAILABLE là "không được phép xem; không tiết lộ dữ liệu hạn chế")
- [ ] 21. 7.2-A_error_handling_backend.md:106@23a5f14 — mã INTERNAL_ERROR khai HTTP 500, trong khi 5.2-A chỉ quy 200 cho GraphQL có lỗi, 400 cho lỗi cú pháp, 401 cho middleware và 400, 401, 413, 415, 429, 503 cho upload, không có 500 (5.2-A mục 2.3 dòng 55; 5.2-A mục 5.2 dòng 331-338)
