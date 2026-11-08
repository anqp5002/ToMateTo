# Góp ý chéo backend và frontend: lệch giữa 6.2-A backend và 6.2-A frontend

## 6.2-A BE và 6.2-A FE

### Nội dung

- [ ] 1. 6.2-A_sequence_diagrams_backend.md:932 và 6.2-A_sequence_frontend.md:519 — theo dõi người dùng (REQ-018, UC-14) thuộc mức Must nhưng cả hai tài liệu chỉ có một dòng chữ nói dùng lại thiết kế, không bên nào có sơ đồ; đã tìm mục 2, 5.3 của backend và mục 13 của frontend (3.4-A mục 2.1; 6.2-A BE mục 5.3)

### Nhất quán

- [ ] 2. 6.2-A_sequence_diagrams_backend.md:666 và 6.2-A_sequence_frontend.md:489 — luồng thử lại trợ lý: sơ đồ backend nhận ID của tin nhắn trả lời thất bại rồi tự lần ra câu hỏi gốc, hợp đồng API cũng ghi ID message thất bại; sơ đồ frontend chỉ ghi retry(messageId) và không nói ID đó là của câu hỏi hay của phản hồi lỗi (5.2-A mục 4; 6.2-A BE)
- [ ] 3. 6.2-A_sequence_diagrams_backend.md:197 và 6.2-A_sequence_frontend.md:108 — gửi lại mã khôi phục bị giới hạn: frontend chờ RATE_LIMITED kèm thời gian chờ để cập nhật bộ đếm gửi lại, còn sơ đồ backend chỉ ném RATE_LIMITED không nêu dữ liệu thời gian chờ trả về (6.2-A FE mục 4; 6.2-A BE mục 3.2)
- [ ] 4. 6.2-A_sequence_diagrams_backend.md:561 và 6.2-A_sequence_frontend.md:354 — bỏ lưu bài: backend vẽ cả savePost lẫn removeSavedPost và setLike (Hình 06), frontend chỉ vẽ savePost và nói thích và theo dõi dùng lại thiết kế; tìm removeSavedPost trong 6.2-A FE không thấy (6.2-A BE mục 3.6; 6.2-A FE mục 13)
