# ToMateTo Flutter

Nền Android/web WP41-S8.1 được giữ, bổ sung Content WP42-S9.4: feed, chi tiết, tạo bài và upload từng ảnh. Các route tài khoản còn là điểm nối cho nhóm Identity. `ToMateToApp(session: ...)` cho phép tiêm SessionStore thật; không có token hardcode.

```shell
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=GRAPHQL_URL=http://localhost:8000/graphql
```

Đặt GRAPHQL_URL theo môi trường chạy. Trình duyệt cần CORS được API cho phép khi khác origin. Màn kiểm tra dùng query feed công khai qua View → Controller → Repository → Transport. Test transport dùng token giả trong MemorySessionStore để kiểm việc đọc token ở từng request. Test fixture không dùng token trong môi trường thật.

Nếu thử trên Android Emulator, dùng địa chỉ máy host của emulator và cấu hình debug phù hợp khi gọi HTTP cục bộ. Dùng HTTPS với API công khai.
