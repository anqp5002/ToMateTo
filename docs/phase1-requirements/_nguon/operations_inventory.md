# Operations Inventory — BE (WBS 1.1.2 — bản gọn)

| Thông tin | Nội dung |
|---|---|
| Owner | BE |
| Reviewer | FE / DB |
| Ngày | 2026-10-14 |
| WBS | 1.1.2 Liệt kê thao tác hệ thống cần có (0.5 ngày) |
| Phạm vi | Chỉ liệt kê thao tác dự kiến, chưa cần input/output chi tiết, chưa cần file:line (để S2) |
| Nguồn | `1.3_system_context.md` (E1-E6), Persona trong docx |

> WBS 1.1.2 chỉ yêu cầu **danh sách thao tác**. Bản trước 24 op chi tiết là dư → gọn còn **14 op**.

## Bảng op (14 dòng: UC | Op dự kiến | Loại | Entity)

### A. BE chủ trì (WBS 1.2.3: tương tác, khám phá, trợ lý AI)

| UC | Op dự kiến | Loại | Entity liên quan |
|---|---|---|---|
| UC-02 Quay random | getRandomDish | query | Dish |
| UC-03 Xem map | getNearbyPlaces | query | Place |
| UC-07 Like/Save | toggleLike | mutation | Like |
| UC-07 Like/Save | savePost (*) | mutation | Collection, CollectionItem |
| UC-08 Follow/Notify | toggleFollow | mutation | Follow |
| UC-08 Follow/Notify | getNotifications | query | Notification |
| UC-09 Report | reportPost | mutation | Report |
| UC-10 Chat gợi ý | createChatSession | mutation | ChatSession |
| UC-10 Chat gợi ý | sendChatMessage | mutation | ChatMessage |
| UC-11 Dùng draft | usePostDraft | mutation | PostDraft |

(*) `savePost` đã gộp `savePost / unsavePost / createCollection` → S2 tách lại nếu cần.

### B. Tham khảo (FE chủ trì ở 1.2.2, BE chỉ dùng để vẽ luồng 1.3.1)

| UC | Op dự kiến | Loại | Entity liên quan |
|---|---|---|---|
| UC-01 Xem feed | getFeed | query | Post, User |
| UC-04 Xem chi tiết | getPostDetail | query | Post, Media |
| UC-05 Đăng bài | createPost | mutation | Post, Media, Place, Dish |
| UC-05 Đăng bài | uploadImage | mutation | Media |

## Ghi chú gọn (thay cho ma trận dài)

* 0 op mồ côi, 0 UC-BE thiếu op (UC-02,03,07,08,09,10,11 đều có op).
* Đã cắt so với bản cũ: `searchDishes, updatePost, deletePost, register, login, saveOnboardingPrefs, getChatHistory, markNotificationRead` → thuộc phần FE (1.2.2) hoặc để S2 chi tiết, không cần ở S1.
* N report ẩn bài, bán kính map, công thức Đang hot: chưa chốt số ở S1, để S2/S6.
