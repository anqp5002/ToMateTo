# Góp ý chéo: lệch giữa các tài liệu backend, frontend và dữ liệu của S6

## 7.2-A BE và 7.2-A FE

### Nội dung

- [ ] 1. 7.2-A_error_handling_backend.md:85@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:34@999e0be — 7.2-A BE mục 3 lỗi con trỏ không hợp lệ chưa có dòng xử lý ở 7.2-A FE: bảng FE chỉ có lỗi dưới trường biểu mẫu (dòng 25) và lỗi mạng hoặc INTERNAL_ERROR khi tải danh sách (dòng 34) (7.2-A BE mục 3; 7.2-A FE)
- [ ] 2. 7.2-A_error_handling_backend.md:86@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:34@999e0be — kích thước trang không hợp lệ ở 7.2-A BE mục 3 không có dòng xử lý nào ở 7.2-A FE (7.2-A BE mục 3; 3.2-A NFR-02)
- [ ] 3. 7.2-A_error_handling_backend.md:87@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:41@999e0be — toạ độ ngoài miền ở 7.2-A BE mục 3 không có dòng ở 7.2-A FE; dòng 41 của FE chỉ nói từ chối quyền vị trí hoặc thiếu toạ độ (7.2-A BE mục 3; 7.2-A FE)
- [ ] 4. 7.2-A_error_handling_backend.md:91@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:40@999e0be — tự theo dõi ở 7.2-A BE mục 3 không có thông báo riêng ở 7.2-A FE; dòng 40 của FE chỉ nói thao tác theo dõi thất bại chung (7.2-A BE mục 3; 7.2-A FE)
- [ ] 5. 7.2-A_error_handling_backend.md:89@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:36@999e0be — ảnh hết hạn và sai mục đích trả VALIDATION_FAILED trong GraphQL ở 7.2-A BE mục 3, nhưng 7.2-A FE xử lý ảnh theo mã HTTP ở dòng 35 và chỉ nhắc ảnh hết hạn ở dòng 36 dành cho 429 và 503 (7.2-A BE mục 3; 7.2-A FE)
- [ ] 6. 7.2-A_error_handling_backend.md:100@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:29@999e0be — RATE_LIMITED áp dụng cho mọi thao tác ở 7.2-A BE mục 3, nhưng 7.2-A FE chỉ có dòng cho gửi mã OTP (dòng 29) và tải ảnh (dòng 36) (7.2-A BE mục 3; 7.2-A FE)
- [ ] 7. 7.2-A_error_handling_backend.md:106@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:34@999e0be — INTERNAL_ERROR ở thao tác ghi không có dòng ở 7.2-A FE: dòng 34 chỉ nói tải danh sách, trong khi FE nêu rõ không suy ra thành công khi mất phản hồi (7.2-A BE mục 3; 7.2-A FE)

### Nhất quán

- [ ] 8. 7.2-A_error_handling_backend.md:100@23a5f14 và 7.2-A_xu_ly_loi_frontend.md:29@999e0be — thông điệp cho người dùng ở 7.2-A BE mục 3 khác chữ ở 7.2-A FE cho các mã LOGIN_FAILED, SESSION_INVALID, RESET_GRANT_INVALID, EMAIL_EXISTS, RESOURCE_MISSING và REQUEST_LIMIT (ví dụ BE "Bạn thao tác quá nhanh" và FE dòng 29 "Bạn đã gửi quá nhiều yêu cầu"), cả hai tài liệu không nói chữ nào được hiển thị (7.2-A BE mục 3; 7.2-A FE)

## 7.1-A BE và 7.1-A.1 DB

### Nhất quán

- [ ] 9. 7.1-A_algorithm_specifications_backend.md:122@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:162@439472c — quay món DB dùng ORDER BY random LIMIT 1 trên catalog; BE mục 5 yêu cầu tập mục tiêu 40 món (70% xu hướng, 30% seed) (7.1-A BE mục 5 dòng 122, 126)
- [ ] 10. 7.1-A_algorithm_specifications_backend.md:180@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:139@439472c — tìm kiếm DB sắp xếp theo type_rank và id; BE mục 7 yêu cầu sắp xếp theo mức phù hợp và id (7.1-A BE mục 7 dòng 180)
- [ ] 11. 7.1-A_algorithm_specifications_backend.md:83@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:249@439472c — DB chỉ công bố snapshot bài và món, trả tag_count bằng 0; 5.3-B S4 yêu cầu công bố cả ba nhóm snapshot nguyên tử (5.3-B S4 mục 3, 5.3-B_schema_specification.md:248@3ec4d83)
- [ ] 12. 7.1-A_algorithm_specifications_backend.md:81@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:262@439472c — DB yêu cầu món trending phải có bài nguồn hợp lệ với viewer; BE mục 3 không mô tả giải thuật đọc trending món (7.1-A BE mục 3 dòng 81-100)
- [ ] 13. 7.1-A_algorithm_specifications_backend.md:142@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:175@439472c — DB cắt caption bài đăng tối đa 200 ký tự cho ngữ cảnh AI; BE mục 6 không quy định giới hạn độ dài này (7.1-A BE mục 6 dòng 142)
- [ ] 14. 7.1-A_algorithm_specifications_backend.md:88@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:217@439472c — DB tính điểm lưu bằng cách khử trùng theo user và lấy MIN(added_at); BE mục 3 dòng 88 chỉ tính số lượt lưu đơn thuần (7.1-A BE mục 3 dòng 88)
- [ ] 15. 7.1-A_algorithm_specifications_backend.md:202@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:127@439472c — chuẩn hóa DB chỉ dùng unaccent không chuyển đ thành d; BE mục 8 dòng 202 bắt buộc chuyển cả đ và Đ thành d (7.1-A BE mục 8 dòng 202)
- [ ] 16. 7.1-A_algorithm_specifications_backend.md:144@23a5f14 và 7.1-A.1_truy_van_chi_muc_db.md:177@439472c — BE mục 6 yêu cầu kiểm tra món, quán, bài được nhắc; DB chỉ có Q20 kiểm tra bài, thiếu truy vấn kiểm tra món và quán (7.1-A BE mục 6 dòng 144)
