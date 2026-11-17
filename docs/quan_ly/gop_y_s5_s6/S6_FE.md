# Góp ý 6.3-A Mockup hi-fi, 6.3-B Design System và 7.2-A Xử lý lỗi frontend

## 6.3-B FE

### Nhất quán

- [ ] 1. 6.3-B_design_system_fe.md:24 — thang cỡ chữ chỉ có 32, 28, 21, 16, 13 px; cả 18 màn dùng cỡ 24 px và 9 màn dùng cỡ 14 px mà 6.3-B không có token tương ứng (6.3-B mục Màu và chữ)
- [ ] 2. 6.3-B_design_system_fe.md:33 — thang bo góc chỉ có 12 và 16 px; chín màn dùng bo góc tròn đầy (rx 99) cho chip và nhãn mà 6.3-B không có token tương ứng (6.3-B mục Khoảng cách và bố cục)
- [ ] 3. 6.3-B_design_system_fe.md:13 — bảng màu chỉ định nghĩa 10 mã màu token; toàn bộ 18 file SVG sử dụng 4 mã màu #E6AA74, #A6422F, #E9C780, #947247 trong gradient nền nhưng không có trong bảng màu (6.3-B FE mục Màu và chữ)

## 6.3-A FE

### Hình thức

- [ ] 4. svg/MH-01.svg:1 — ba nút hành động không vừa bề ngang khung nội dung 332 px: hàng đầu đã dùng 29→294.59 px, nút "Đăng ký" rộng 91.97 px bị đẩy xuống hàng thứ hai và chỉ chiếm 91.97 px, chừa trống 240 px bên phải; nhìn ảnh thành khối nút hình chữ L lệch (6.3-B mục Khoảng cách và bố cục, khung nội dung và padding khối chính)
- [ ] 5. svg/MH-06.svg:1 — bốn mục lọc hàng đầu chạy tới x=327.03 nên không còn chỗ cho mục "Tìm kiếm" 99.92 px, mục này rơi xuống hàng thứ hai đứng một mình và chừa trống 232 px bên phải; trên ảnh hàng lọc bị gãy dòng (6.3-B mục Khoảng cách và bố cục, thang khoảng cách 4/8/12/16/24/32)
- [ ] 6. svg/MH-07.svg:1 — hàng "Công thức" không có rect nút, chỉ có một path mũi tên 6×10 px và chữ 16 px, nên vùng chạm của hàng này dưới 44 px trong khi 6 nút còn lại trên màn đều cao đúng 44 px (6.3-B mục Khoảng cách và bố cục, vùng bấm tối thiểu 44 px)
- [ ] 7. svg/MH-11.svg:1 — ô tick "Giới thiệu" là rect 13×13 px, vùng chạm nhỏ hơn 44 px và nhỏ hơn mọi nút khác trên màn; trên ảnh ô tick chỉ bằng một chấm xanh cạnh dòng chữ (6.3-B mục Khoảng cách và bố cục, vùng bấm tối thiểu 44 px)

### Nội dung

- [ ] 8. 6.3-A_mockup_hifi_fe.md:86 — mục Điểm cần chú ý của MH-06 không nói khách chưa đăng nhập bấm Thích hoặc Lưu trên thẻ bài thì xảy ra điều gì; tìm QD-01, QD-02 trong cả 6.3-A không thấy (2.1-B mục 3 về QD-01 và QD-02; 6.3-A mục MH-06)
- [ ] 9. 6.3-A_mockup_hifi_fe.md:94 — MH-07 không nói khách chưa đăng nhập bấm Thích, Lưu hoặc Theo dõi thì xảy ra điều gì; tìm QD-01, QD-02 trong cả 6.3-A không thấy (2.1-B mục 3 về QD-01 và QD-02; 6.3-A mục MH-07)
- [ ] 10. 6.3-A_mockup_hifi_fe.md:94 — màn MH-07 chỉ mô tả trạng thái hiển thị chi tiết bài và bài không còn khả dụng, không có mô tả trạng thái đang tải (skeleton loading) (6.3-B FE mục Thành phần dùng chung, 6.3-A FE mục MH-07)
- [ ] 11. 6.3-A_mockup_hifi_fe.md:118 — màn MH-10 Hồ sơ không có mô tả trạng thái rỗng và hành vi gợi ý tạo bài khi người dùng chưa có bài viết nào (6.3-B FE mục Thành phần dùng chung, 6.3-A FE mục MH-10)
- [ ] 12. 6.3-A_mockup_hifi_fe.md:150 — màn MH-14 Thông báo không có mô tả trạng thái rỗng khi người dùng chưa có thông báo nào (6.3-B FE mục Thành phần dùng chung, 6.3-A FE mục MH-14)

### Nhất quán

- [ ] 13. svg/MH-01.svg:1 — cả 18 màn đều có nhãn đỏ IN HOA 13 px "MH-xx" nằm ngay trên tiêu đề màn, bên trong thân giao diện, nên nhãn đánh số của bản vẽ lọt vào màn hình người dùng; nhìn ảnh MH-01 thấy chữ "MH-01" đứng trên "Đăng nhập" (6.3-B mục Thành phần dùng chung, danh sách thành phần không có nhãn số màn)
- [ ] 14. svg/MH-06.svg:1 — năm màn MH-06, MH-10, MH-13, MH-15, MH-18 dùng cùng một cấu trúc thẻ 5 phần với cùng kích thước: khung 332×335.3 px, ảnh gradient 298×144, chip 25 px, tên món 21 px, nút "Xem bài" 44 px; mở năm ảnh cạnh nhau thấy cùng một thẻ, khác nhau chỉ ở chuỗi chữ và màu gradient (6.3-B mục Thành phần dùng chung, Post card gồm ảnh + tên món + tác giả + hành động xem bài)
- [ ] 15. svg/MH-16.svg:1 — mọi tiêu đề mục đều bị gắn thêm một viên thuốc nhỏ phía trên; riêng MH-16 viên thuốc 80.7×25 px chép lại đúng chữ "Xu hướng" của tiêu đề màn nên trên ảnh thành hai dòng chữ trùng nhau, đường cơ sở cách nhau 52 px (6.3-B mục Thành phần dùng chung, Chip dùng cho nhãn ngắn như khoảng giá hoặc trạng thái)

## 7.2-A FE

### Hình thức

- [ ] 16. 7.2-A_xu_ly_loi_frontend.md:35 — mô tả hiện lỗi gửi ảnh chung đối với lỗi 415 nhưng không có chuỗi văn bản thông báo tiếng Việt cụ thể trong ngoặc kép (7.2-A FE mục Bảng xử lý theo tình huống)
- [ ] 17. 7.2-A_xu_ly_loi_frontend.md:40 — mô tả Báo lỗi cạnh hành động hoặc banner ngắn nhưng không có chuỗi thông báo tiếng Việt cụ thể cho các thao tác thích, lưu và theo dõi (7.2-A FE mục Bảng xử lý theo tình huống)

### Nội dung

- [ ] 18. 7.2-A_xu_ly_loi_frontend.md:29 — bảng xử lý chỉ định nghĩa RATE_LIMITED cho tình huống gửi OTP, thiếu xử lý mã lỗi RATE_LIMITED khi người dùng gửi quá 10 báo cáo bài trong 1 giờ (5.2-A mục 12.5, 7.2-A FE mục Bảng xử lý theo tình huống)
- [ ] 19. 7.2-A_xu_ly_loi_frontend.md:42 — dòng 42 ghi AI lỗi hoặc timeout nhưng không quy định ngưỡng thời gian chờ 30 giây trước khi kích hoạt xử lý quá hạn (3.2-A mục NFR-04, 5.2-A mục 7.1, 7.2-A FE mục Bảng xử lý theo tình huống)
