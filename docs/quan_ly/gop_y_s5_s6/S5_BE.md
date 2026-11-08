# Góp ý 6.1-A Thiết kế lớp backend và 6.2-A Sơ đồ tuần tự backend

## 6.1-A BE

### Hình thức

- [ ] 1. 6.1-A_class_diagrams_backend.md:902 — TransactionManager, CursorCodec và ContextFactory mang nhãn `<<service>>`, trong khi §3 đếm 10 service và xếp chúng vào nhóm hỗ trợ hoặc dùng chung (6.1-A BE mục 3, mục 5.2 và mục 5.7)

### Nội dung

- [ ] 2. 6.1-A_class_diagrams_backend.md:27 — J1 Background Job Runner ở 5.1-A/B không có lớp nào; tài liệu đếm 22 thành phần và bỏ J1, trong khi catalogue khai 23; đã đọc §4.1–§4.5, §5.1–§5.7, §9 (5.1-A/B mục 1 và 2.3)
- [ ] 3. 6.1-A_class_diagrams_backend.md:1234 — CreatePostInput có `tags`, hợp đồng v1 không có trường này và ghi rõ thẻ bị hoãn (5.2-A mục 4.3 và ghi chú)
- [ ] 4. 6.1-A_class_diagrams_backend.md:1227 — RegisterDeviceInput dùng `fcmToken`, API §4.3 dùng `pushToken`; chính API §12.2 lại dùng `fcmToken` (5.2-A mục 4.3 và 12.2)
- [ ] 5. 6.1-A_class_diagrams_backend.md:1261 — `myCollections` trỏ CollectionService nhưng lớp không có phương thức liệt kê; chỉ CollectionRepository.listByUser làm việc này (6.1-A BE §4.3, §5.2, §5.3; 5.1-A/B thành phần B6 `listCollections`)
- [ ] 6. 6.1-A_class_diagrams_backend.md:1262 — `collectionItems` trỏ FeedQueryService nhưng lớp chỉ có listFeed, getPost, listPostsByAuthor; CollectionService.listItems không được nối (6.1-A BE §4.3, §5.2; 5.1-A/B thành phần B6 `listCollectionItems`)
- [ ] 7. 6.1-A_class_diagrams_backend.md:583 — savePost và removeSavedPost khai collectionId bắt buộc, hợp đồng cho phép null (5.2-A mục 4.2)
- [ ] 8. 6.1-A_class_diagrams_backend.md:1190 — Tài liệu khai 19 bảng hiện có cộng một bảng chờ theo 5.3-A, trong khi 5.3-A bản hiện hành có 25 bảng (5.3-A mục 2; 5.3-B mục 2)
- [ ] 9. 6.1-A_class_diagrams_backend.md:1089 — User thiếu email_normalized, username_normalized, public_profile_fields, avatar_media_id, cover_media_id, token_version, is_active, updated_at; có avatarUrl, coverUrl, isPrivate không phải cột (5.3-B T01)
- [ ] 10. 6.1-A_class_diagrams_backend.md:1346 — Nói users.username bắt buộc và duy nhất; T01 cho phép NULL và duy nhất trên username_normalized (5.3-B T01)
- [ ] 11. 6.1-A_class_diagrams_backend.md:1093 — Post có likesCount, cookTimeMinutes, servings không có cột; T09 ghi không thêm likes_count (5.3-B T09)
- [ ] 12. 6.1-A_class_diagrams_backend.md:1094 — PostImage lưu url; T10 dùng media_id UUID tham chiếu media_assets, không có cột url (5.3-B T10)
- [ ] 13. 6.1-A_class_diagrams_backend.md:1095 — PostTag có createdAt; T11 chỉ có post_id và tag_id (5.3-B T11)
- [ ] 14. 6.1-A_class_diagrams_backend.md:1097 — Collection thiếu name_normalized, cột NOT NULL và là phần của khóa duy nhất theo chủ (5.3-B T14)
- [ ] 15. 6.1-A_class_diagrams_backend.md:1100 — Report thiếu original_post_id và evidence_snapshot; post_id phải nullable; §7 đặt duy nhất trên (reporter_id, post_id) thay vì original_post_id (5.3-B T16)
- [ ] 16. 6.1-A_class_diagrams_backend.md:1101 — Notification dùng payload và read; T17 dùng actor_id, post_id, read_at; kiểu chỉ LIKE, SAVE, FOLLOW trong khi §5.6 có NEW_POST_FROM_FOLLOWING (5.3-B T17)
- [ ] 17. 6.1-A_class_diagrams_backend.md:1103 — ChatMessage thiếu reply_to_id, status, processing_version, processing_expires_at; có imageUrl không có cột; §10 L7 vẫn nói thiếu cột trạng thái (5.3-B T19)
- [ ] 18. 6.1-A_class_diagrams_backend.md:1104 — UserDevice dùng fcmToken và deviceType; T04 dùng push_token và platform; §7 khai duy nhất (user_id, fcm_token) thay vì push_token (5.3-B T04)
- [ ] 19. 6.1-A_class_diagrams_backend.md:1105 — PasswordReset liên kết qua email, không có user_id; T02 có user_id FK cùng failed_attempts, otp_expires_at, reset_token_hash, consumed_at (5.3-B T02)
- [ ] 20. 6.1-A_class_diagrams_backend.md:1106 — RevokedToken có id và khóa chính id; T03 dùng jti làm khóa chính và không có cột id (5.3-B T03)
- [ ] 21. 6.1-A_class_diagrams_backend.md:1107 — TrendingDishSnapshot có postCount, likeCount, trendingScore, snapshotDate; T22 chỉ run_id, dish_id, score; khóa (dish_id, snapshot_date) không tồn tại (5.3-B T22)
- [ ] 22. 6.1-A_class_diagrams_backend.md:1108 — Không có lớp cho T20 trending_runs, T21 và T23 snapshot, T24 media_cleanup_jobs, T25 user_blocks; đã đọc §4.1–§4.5, §5.5, §5.7, §7 (5.3-B T20, T21, T23, T24, T25)
- [ ] 23. 6.1-A_class_diagrams_backend.md:1108 — MediaUpload ghi chờ lược đồ với id kiểu str; T05 đã có media_assets kiểu UUID với state, provider, storage_key, input_size_bytes, stored_size_bytes, mime_type, deleted_at; §10 L2 và §12 vẫn nói chưa có bảng (5.3-B T05)
- [ ] 24. 6.1-A_class_diagrams_backend.md:1134 — Enum có IOS, ANDROID, WEB; T04 CHECK chỉ nhận android và web (5.3-B T04)
- [ ] 25. 6.1-A_class_diagrams_backend.md:1131 — Nói giá lưu chữ thường; T09 CHECK dùng giá trị chữ hoa; §8.3 lặp lại chữ thường (5.3-B T09)

### Nhất quán

- [ ] 26. 6.1-A_class_diagrams_backend.md:1336 — §9 nói hai job nền, trong khi J1 ở 5.1-A/B chạy bốn job định kỳ và §1.3 cũng ghi hai (5.1-A/B mục 2.3–2.4)
- [ ] 27. 6.1-A_class_diagrams_backend.md:13 — Số thành phần 22 không khớp nguồn 23 và không khớp 24 ở API §7.2, nơi có P0, B11, X1–X5 không tồn tại trong 5.1-A/B (5.1-A/B mục 1; 5.2-A mục 7.2)
- [ ] 28. 6.1-A_class_diagrams_backend.md:1038 — Hậu điều kiện resetPassword nói tăng phiên bản phiên nhưng không lớp nào có phương thức tăng; phụ thuộc của service cũng không có (6.1-A BE §4.1, §5.2, §10 L4)
- [ ] 29. 6.1-A_class_diagrams_backend.md:1348 — Nói lược đồ chỉ có is_private, nhưng T01 không có cột này mà có public_profile_fields (5.3-B T01)
- [ ] 30. 6.1-A_class_diagrams_backend.md:1349 — Nói bảng posts không có cột feeling, nhưng T09 có cột feeling (5.3-B T09)
- [ ] 31. 6.1-A_class_diagrams_backend.md:964 — Sơ đồ gói vẽ BIZ --> SHARED nhưng SHARED chứa ContextFactory gọi SessionTokenService thuộc business, tạo vòng không được vẽ (6.1-A BE mục 2.2, mục 3 và mục 4.5)
- [ ] 32. 6.1-A_class_diagrams_backend.md:488 — Sơ đồ 4.2 chỉ có FeedQueryService gọi PostRepository, trong khi §5.2 khai thêm LikeRepository và CollectionRepository (6.1-A BE mục 4.2 và mục 5.2)
- [ ] 33. 6.1-A_class_diagrams_backend.md:960 — Sơ đồ 4.5 chỉ có WriteAuthorizationPolicy gọi PostRepository, trong khi §5.2 và §6 khai ba repository (6.1-A BE mục 4.5, mục 5.2 và mục 6)
- [ ] 34. 6.1-A_class_diagrams_backend.md:1005 — mục 5.2 và 5.3 của 6.1-A không có các lớp MediaCleanupRepository, BlockRepository và các phương thức bumpTokenVersion, invalidateOpenForUser, findByGrantHash, claimReply, completeReply, buildFallback mà sơ đồ tuần tự backend gọi; 6.2-A tự ghi đây là phần mở rộng cần đồng bộ sang 6.1-A, nhưng bản 6.1-A mới hơn (07/11) chưa nhận; đã tìm toàn tệp bằng tên từng phương thức (6.2-A BE mục 5.2.2 và mục 5.4)

## 6.2-A BE

### Nội dung

- [ ] 35. 6.2-A_sequence_diagrams_backend.md:89 — Use Case UC-01 Đăng ký tài khoản là yêu cầu Must trong ma trận MoSCoW nhưng không có sơ đồ tuần tự riêng (3.4-A mục 2.2, 6.2-A BE mục 2)
- [ ] 36. 6.2-A_sequence_diagrams_backend.md:930 — Use Case UC-05 Xem feed là yêu cầu Must trong ma trận MoSCoW nhưng Backend không có sơ đồ tuần tự riêng (3.4-A mục 2.2, 6.2-A BE mục 5.3)
