# Góp ý 6.1-A Thiết kế lớp backend và 6.2-A Sơ đồ tuần tự backend

## 6.1-A BE

### Nội dung

- [ ] 1. 6.1-A_class_diagrams_backend.md:1409@3571426 — UnregisterDeviceInput dùng `fcmToken`, trong khi API khai unregisterDevice nhận `pushToken` (5.2-A mục 12.2)
- [ ] 2. 6.1-A_class_diagrams_backend.md:645@3571426 — SocialResolver khai savePost và removeSavedPost với collectionId không có dấu `?`, hợp đồng cho phép vắng (5.2-A mục 4.2)
- [ ] 3. 6.1-A_class_diagrams_backend.md:397@3571426 — PostMutationResolver có phương thức reportPost nhưng sơ đồ lớp không có cạnh nối tới SocialInteractionService, trong khi bảng phụ thuộc ghi resolver này phụ thuộc SocialInteractionService (6.1-A BE mục 5.1; 5.1-A/B mục 2.3)
- [ ] 4. 6.1-A_class_diagrams_backend.md:679@3571426 — CollectionService được khai ở mục 4.3 nhưng không có trong node nào của sơ đồ gói business (dòng 106–111), dù bảng mục 3 tính nhóm business là 17 lớp và các node chỉ liệt kê 16 lớp (6.1-A BE mục 3 và mục 4.3)

### Nhất quán

- [ ] 5. 6.1-A_class_diagrams_backend.md:106@3571426 — mã B11 đến B16 dùng làm tên node gói ở mục 3 trùng ký hiệu với mã thành phần B1 đến B10 của 5.1-A/B và với B11 của 5.2-A nghĩa là job nền, nên một ký hiệu mang hai nghĩa (5.1-A/B mục 2.3; 5.2-A mục 7)

## 6.2-A BE

### Nội dung

- [ ] 6. 6.2-A_sequence_diagrams_backend.md:89@ed27b57 — Use Case UC-01 Đăng ký tài khoản là yêu cầu Must trong ma trận MoSCoW nhưng không có sơ đồ tuần tự riêng (3.4-A mục 2.2, 6.2-A BE mục 2)
- [ ] 7. 6.2-A_sequence_diagrams_backend.md:930@ed27b57 — Use Case UC-05 Xem feed là yêu cầu Must trong ma trận MoSCoW nhưng Backend không có sơ đồ tuần tự riêng (3.4-A mục 2.2, 6.2-A BE mục 5.3)
