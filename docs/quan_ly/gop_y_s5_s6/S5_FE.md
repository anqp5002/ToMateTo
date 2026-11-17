# Góp ý 6.1-A Thiết kế class provider frontend và 6.2-A Sơ đồ tuần tự frontend

## 6.1-A FE

### Nội dung

- [ ] 1. 6.1-A_class_provider_frontend.md:592 — vẫn còn từ góp ý trước (Class FE AppFailure thiếu retryAfter): AppFailure có requestId nhưng không có retryAfterSeconds, trong khi AcceptedPayload trả trường này và RATE_LIMITED kèm thời gian chờ (5.2-A mục 6 và 12.1)
- [ ] 2. 6.1-A_class_provider_frontend.md:598 — FailureKind chỉ có validation, unauthenticated, forbidden, notAvailable, serviceUnavailable, outcomeUnknown; không có NOT_FOUND, ALREADY_EXISTS, CONFLICT, RATE_LIMITED, INTERNAL_ERROR của API (5.2-A mục 6)
- [ ] 3. 6.1-A_class_provider_frontend.md:1213 — vẫn còn từ góp ý trước (FE-SQ10): DiscoveryRepository không có phương thức cho assistantSessions và §5 không có model AssistantSession; đã tìm §4.34–§4.38 và bảng Model/DTO (5.2-A mục 4.2)
- [ ] 4. 6.1-A_class_provider_frontend.md:900 — vẫn còn từ góp ý trước (FE-SQ04): ContentRepository không có myPosts hoặc profilePosts, ProfileController không tải bài; đã tìm §4.19–§4.21, §4.30 (5.2-A mục 4.2)

### Nhất quán

- [ ] 5. 6.1-A_class_provider_frontend.md:168 — AuthView gọi RecoveryController (C26) trong khi 5.1-A FE khai phụ thuộc của C01 chỉ gồm C02, C15, C16 (5.1-A FE mục 3)

## 6.2-A FE

### Hình thức

- [ ] 6. 6.2-A_sequence_frontend.md:127 — vẫn còn từ góp ý trước ([P1] FE-SQ02): dòng thông điệp chứa dấu chấm phẩy làm Mermaid parser văng lỗi cú pháp, sơ đồ không hiển thị (6.2-A FE mục 4)

### Nội dung

- [ ] 7. 6.2-A_sequence_frontend.md:101 — vẫn còn từ góp ý trước ([P2] FE-SQ02): nhánh đổi email đưa về stage=email nhưng sơ đồ vẫn đi thẳng tiếp tới verifyOtp thay vì quay lại bước gửi OTP cho email mới (6.2-A FE mục 4)
- [ ] 8. 6.2-A_sequence_frontend.md:163 — vẫn còn từ góp ý trước ([P3] FE-SQ03): mũi tên tải thêm truyền page.after trực tiếp thay vì đối tượng PageInput có first và after (5.2-A mục 12.1, mục 12.3)
- [ ] 9. 6.2-A_sequence_frontend.md:240 — vẫn còn từ góp ý trước ([P2] FE-SQ04): mất phản hồi khi đăng bài dừng ở outcomeUnknown mà không có bước xác minh qua thao tác kiểm tra bài đã tạo (6.2-A FE mục 6)
- [ ] 10. 6.2-A_sequence_frontend.md:285 — vẫn còn từ góp ý trước ([P1] FE-SQ05): mũi tên sửa bài truyền mảng images trực tiếp ngoài input và thiếu trường position trong từng phần tử ảnh (5.2-A mục 12.1, mục 12.3)
- [ ] 11. 6.2-A_sequence_frontend.md:515 — Use Case UC-01 Đăng ký tài khoản là yêu cầu Must trong ma trận MoSCoW nhưng không có sơ đồ tuần tự riêng (3.4-A mục 2.2, 6.2-A FE mục 13)
- [ ] 12. 6.2-A_sequence_frontend.md:519 — thao tác Thích bài của người dùng đã đăng nhập thuộc UC-13 là yêu cầu Must nhưng không có sơ đồ tuần tự riêng (3.4-A mục 2.1, 6.2-A FE mục 13)
