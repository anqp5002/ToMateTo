# ToMateTo Flutter

Khung Android/web cho WP41-S8.1. Giao diện kiểm tra kết nối là màn tạm của S8. Các route tài khoản và nội dung là điểm nối để bổ sung màn thật ở các sprint sau.

```shell
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=GRAPHQL_URL=http://localhost:8000/graphql
```

Đặt GRAPHQL_URL theo môi trường chạy. Trình duyệt cần CORS được API cho phép khi khác origin. Màn kiểm tra dùng query feed công khai qua View → Controller → Repository → Transport. Test transport dùng token giả trong MemorySessionStore để kiểm việc đọc token ở từng request. Test fixture không dùng token trong môi trường thật.

Nếu thử trên Android Emulator, dùng địa chỉ máy host của emulator và cấu hình debug phù hợp khi gọi HTTP cục bộ. Dùng HTTPS với API công khai.

## Luồng tài khoản S9

Flutter cần endpoint `/graphql` của backend S9 và một PostgreSQL dev đã có schema
tài khoản/bộ sưu tập. Backend dùng `DATABASE_URL`, `JWT_SECRET`, `OTP_PEPPER`
và danh sách origin web trong `WEB_ORIGINS`. Xem README gốc để chuẩn bị môi trường.

```powershell
flutter run -d chrome --web-port=8080 --dart-define=GRAPHQL_URL=http://localhost:8000/graphql
```

Trên Android Emulator, dùng `http://10.0.2.2:8000/graphql` với bản debug. Lấy liên kết
**Đăng nhập** ở đầu trang, chuyển qua **Tạo tài khoản**, nhập thông tin và gửi.
Đăng ký thành công mở phiên ngay. Thử đăng xuất, đăng nhập sai mật khẩu và kiểm tra
email vẫn còn trong form. Khi mất mạng lúc đăng xuất, app cho phép thử lại hoặc chỉ
kết thúc phiên trên thiết bị.

Màn nội dung hiện giữ điểm nối S8. Các thao tác feed, thích và lưu cần tích hợp
nhánh Nội dung/Social để kiểm thử đầy đủ việc quay lại ngữ cảnh.
