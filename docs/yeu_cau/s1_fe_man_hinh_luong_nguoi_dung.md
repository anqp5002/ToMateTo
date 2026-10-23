# S1 Danh sách màn hình và luồng người dùng cần có

> Dự án: ToMateTo  
> WBS: 1.1.1 — Liệt kê màn hình và luồng người dùng cần có  
> Owner: FE | Reviewer: Lead đề xuất, cần nhóm xác nhận | Approver: Lead  
> Sprint: S1 | Tuần: 12–18/10/2026

## 1. Mục đích

Tài liệu đề xuất các màn hình và luồng người dùng phục vụ phạm vi v1.0 của ToMateTo. Đây là đầu vào cho workshop actor/use case WBS 1.2.1, đặc tả UC và wireframe S2. Danh sách chưa phải thiết kế giao diện đã duyệt hoặc bản mô tả sản phẩm đã được triển khai.

Các lựa chọn chưa được duyệt được ghi rõ là đề xuất hoặc cần quyết. Tài liệu chưa gán route kỹ thuật, tên API hoặc bảng dữ liệu.

## 2. Người dùng và phạm vi

### 2.1 Actor dự kiến

| Actor | Mục tiêu | Quyền dự kiến cần xác nhận |
|---|---|---|
| Khách chưa đăng nhập | Xem thử nội dung và tìm ý tưởng ăn uống | Đề xuất xem feed, chi tiết, tìm kiếm và nội dung khám phá; chưa được đăng bài hoặc thực hiện tương tác cá nhân |
| Người dùng đã đăng nhập | Chia sẻ, lưu, theo dõi và quản lý hồ sơ | Đăng bài, thích, lưu, theo dõi, xem thông báo và quản lý thông tin của mình |
| Người đăng bài | Kiểm soát nội dung do mình tạo | Đề xuất được sửa/xóa bài của mình; cần nhóm chốt vì Vision chưa liệt kê rõ quyền sửa/xóa |

Người đăng bài là người dùng trong ngữ cảnh sở hữu bài, không phải loại tài khoản riêng. Chủ quán là stakeholder chịu ảnh hưởng; chưa có yêu cầu tài khoản chủ quán hoặc màn quản lý quán. Không bổ sung actor Admin khi trang quản trị nằm ngoài phạm vi.

### 2.2 Nhóm phạm vi

- **Lõi:** tài khoản, nội dung và tương tác, theo thứ tự ưu tiên trong Vision.
- **Khám phá:** tìm kiếm, xu hướng, quán gần và quay món.
- **AI:** hỏi đáp trên dữ liệu hệ thống và soạn bài nháp.
- **Đề xuất cần duyệt:** sửa/xóa bài, quản lý chi tiết bộ sưu tập, đổi mật khẩu trong phiên và các tiện ích vượt phần Vision mô tả rõ.

Phân nhóm này hỗ trợ lập danh sách, không thay thế MoSCoW S2. Vision nói cắt bản đồ/quay món trước khi trễ, sau đó AI; tìm kiếm và xu hướng cần được chốt mức ưu tiên riêng.

Ngoài phạm vi: đặt món, thanh toán, giao hàng, bình luận, video/story/livestream, nhắn tin giữa người dùng, trang quản trị và iOS.

## 3. Danh sách màn hình dự kiến

ID MH dùng để truy vết trong tài liệu, không phải tên route hoặc mã UC chính thức. Một mục có thể được gộp thành tab, sheet hoặc trạng thái trong wireframe; không bắt buộc mỗi mục trở thành một màn độc lập.

| ID | Màn hình hoặc khu vực chức năng | Người sử dụng | Mục tiêu và nội dung chính | Hành động chính | Phạm vi |
|---|---|---|---|---|---|
| MH-01 | Đăng nhập | Khách | Nhập thông tin xác thực và biết lỗi đăng nhập | Đăng nhập, sang đăng ký hoặc khôi phục mật khẩu | Lõi |
| MH-02 | Đăng ký | Khách | Tạo tài khoản với thông tin cần thiết | Nhập, xác nhận và gửi đăng ký | Lõi |
| MH-03 | Khôi phục mật khẩu | Khách | Nhập email và xác minh OTP trong hai trạng thái cùng màn | Gửi OTP, xác minh, gửi lại, đổi email, hủy | Lõi |
| MH-05 | Đặt mật khẩu mới | Người đang khôi phục | Chọn mật khẩu mới sau xác minh | Lưu và trở lại đăng nhập | Lõi |
| MH-06 | Feed | Khách và user | Xem bài mới hoặc đang hot | Đổi nhóm bài, mở chi tiết, tải thêm | Lõi |
| MH-07 | Chi tiết bài | Khách và user | Xem món, ảnh, quán, giá, địa chỉ và nội dung chia sẻ | Thích, lưu, theo dõi tác giả, báo cáo nếu đủ quyền | Lõi |
| MH-08 | Tạo bài đăng | User | Nhập trải nghiệm món ăn và kiểm tra trước khi đăng | Chọn ảnh, nhập thông tin, đăng hoặc hủy | Lõi |
| MH-09 | Chỉnh sửa bài | Chủ bài | Cập nhật nội dung của mình | Lưu hoặc hủy thay đổi | Đề xuất cần duyệt |
| MH-10 | Hồ sơ cá nhân | User; hồ sơ công khai nếu duyệt | Xem thông tin và nội dung của bản thân hoặc tác giả | Mở bài, sửa hồ sơ của mình, theo dõi người khác | Lõi; phạm vi công khai cần chốt |
| MH-11 | Chỉnh sửa hồ sơ | User | Quản lý thông tin hồ sơ được phép thay đổi | Lưu hoặc hủy | Lõi; danh sách trường cần chốt |
| MH-12 | Bộ sưu tập | User | Tìm lại và tổ chức bài đã lưu | Mở bộ sưu tập; tạo/đổi tên/xóa nếu duyệt | Lõi; quyền quản lý cần chốt |
| MH-13 | Chi tiết bộ sưu tập | User | Xem nội dung đã lưu theo nhóm | Mở bài, bỏ lưu hoặc chuyển nhóm nếu duyệt | Lõi; thao tác nâng cao cần chốt |
| MH-14 | Thông báo | User | Biết những sự kiện cá nhân liên quan | Xem, mở nội dung liên quan, đánh dấu đã đọc | Lõi; loại sự kiện cần chốt |
| MH-15 | Tìm kiếm và khám phá | Khách và user đề xuất | Tìm theo món/khu vực và tiêu chí được duyệt | Nhập từ khóa, lọc, mở kết quả | Khám phá |
| MH-16 | Xu hướng | Khách và user đề xuất | Xem món hoặc nội dung nổi bật | Chọn mục để xem nội dung liên quan | Khám phá; có thể gộp MH-15 |
| MH-17 | Quán gần theo vị trí | Khách và user đề xuất | Tìm địa điểm quanh vị trí được chọn | Cho phép vị trí hoặc chọn khu vực, xem danh sách/bản đồ | Khám phá; hình thức hiển thị cần chốt |
| MH-18 | Quay món | Khách và user đề xuất | Nhận gợi ý khi chưa biết ăn gì | Yêu cầu gợi ý, xem kết quả, thử lại | Khám phá |
| MH-19 | Trò chuyện với trợ lý | User đề xuất | Hỏi món/quán/bài trên dữ liệu hệ thống và yêu cầu draft | Gửi câu hỏi, xem gợi ý, chuyển draft sang tạo bài | AI |

**Số mục hiện tại: 18 khu vực/màn hình dự kiến.** Nhập email và xác minh OTP là hai trạng thái của MH-03. Các mã MH còn lại được giữ nguyên. Không tính mỗi thông báo thành công, hộp thoại, bộ lọc hoặc trạng thái lỗi thành một màn riêng.

### 3.1 Thành phần không nhất thiết là màn độc lập

| Thành phần | Gắn với | Nội dung |
|---|---|---|
| Điều hướng chung | Feed và nhóm chức năng chính | Đi tới nội dung, khám phá, tạo bài và hồ sơ; bố cục chọn ở wireframe |
| Chọn nơi lưu | Chi tiết bài hoặc card bài | Chọn bộ sưu tập; đề xuất tạo mới tại chỗ nếu cần |
| Báo cáo nội dung | Chi tiết bài | Chọn lý do, gửi và nhận phản hồi |
| Xác nhận xóa | Bài của mình | Nêu hậu quả và yêu cầu xác nhận; chỉ thêm sau duyệt quyền xóa |
| Phóng to ảnh | Chi tiết bài | Xem ảnh rõ hơn; khả năng zoom/swipe cần wireframe xác định |
| Kết quả quay món | MH-18 | Hiển thị món và đường tới nội dung liên quan; không cần màn riêng mặc định |
| Draft trợ lý | MH-19 | Nội dung đề xuất và nút chuyển sang MH-08 để người dùng rà soát |
| Xác nhận khôi phục thành công | MH-05 | Cho biết đã đổi mật khẩu và đường trở lại login |
| Đăng xuất | Hồ sơ hoặc menu tài khoản | Kết thúc phiên; vị trí và xác nhận cần chốt |

## 4. Luồng người dùng chính

Mã L dùng liên kết màn và nhu cầu; mã UC chính thức sẽ được nhóm quyết tại workshop. Luồng lỗi dưới đây là yêu cầu thiết kế dự kiến, chưa tuyên bố hệ thống đã xử lý.

### L-01 Xem thử nội dung trước khi đăng nhập

- **Mục tiêu:** người mới hiểu giá trị ứng dụng trước khi tạo tài khoản.
- **Đề xuất:** mở MH-06 → chọn bài → MH-07 → quay lại danh sách.
- **Nhánh:** nếu muốn thích/lưu/đăng bài thì chuyển xác thực; hủy xác thực vẫn xem nội dung được.
- **Trạng thái:** loading, chưa có bài, lỗi tải, bài không còn khả dụng.
- **Cần quyết:** cho phép guest xem các chức năng nào; màn mở đầu và hành vi sau đăng nhập.

### L-02 Đăng ký và bắt đầu sử dụng

- **Luồng:** từ lời mời đăng ký hoặc MH-01 → MH-02 → nhập thông tin → gửi → nhận kết quả → đến vị trí nhóm quy định.
- **Nhánh:** thiếu/sai thông tin, định danh đã dùng, lỗi kết nối, hủy.
- **Cần quyết:** trường bắt buộc, xác minh tài khoản, điều khoản, có tự đăng nhập sau đăng ký hay không.
- **Không mặc định:** cần onboarding hoặc thu sở thích ngay lúc đăng ký.

### L-03 Đăng nhập và tiếp tục thao tác

- **Luồng:** yêu cầu thao tác cá nhân → MH-01 → xác thực → trở về ngữ cảnh trước đó và tiếp tục nếu người dùng xác nhận.
- **Nhánh:** sai thông tin, account không khả dụng, lỗi kết nối, hủy login.
- **Cần quyết:** tự tiếp tục hay yêu cầu bấm lại; cách giữ dữ liệu trước khi chuyển login; thời hạn phiên.

### L-04 Khôi phục mật khẩu

- **Luồng:** MH-01 → MH-03 nhập email → MH-03 xác minh OTP → MH-05 → kết quả → MH-01. Đổi email trở lại trạng thái nhập email trong MH-03; hủy trở về MH-01.
- **Nhánh:** xác minh thất bại/hết hạn, gửi lại bị giới hạn, mật khẩu chưa hợp lệ, kết nối lỗi.
- **Cần quyết:** hiệu lực và giới hạn OTP gửi qua email; thông tin phản hồi tránh lộ account; chính sách mật khẩu.

### L-05 Xem feed và chi tiết bài

- **Luồng:** MH-06 → xem mới nhất/đang hot → tải thêm → mở MH-07 → quay lại giữ ngữ cảnh danh sách.
- **Nhánh:** danh sách rỗng, lỗi tải đầu/tải thêm, bài bị xóa/ẩn hoặc ảnh không tải được.
- **Cần quyết:** ý nghĩa đang hot, cách cập nhật nội dung, dữ liệu card và detail; không chốt thuật toán ở đây.

### L-06 Tạo bài chia sẻ

- **Luồng:** user chọn tạo bài → MH-08 → chọn ảnh và nhập món/quán/giá/địa chỉ → rà soát → gửi → nhận kết quả → xem bài hoặc về feed.
- **Nhánh:** thiếu trường cần thiết, ảnh không hợp lệ, upload/gửi thất bại, bấm gửi lặp, hủy khi chưa lưu.
- **Đề xuất:** không xóa dữ liệu nhập khi thất bại; tránh hiển thị thành công nếu chưa xác nhận kết quả.
- **Cần quyết:** trường bắt buộc, giới hạn ảnh, cách nhập quán/vị trí, hỗ trợ công thức, lưu nháp và quyền sửa/xóa.

### L-07 Sửa hoặc xóa bài của mình

- **Trạng thái phạm vi:** đề xuất cần duyệt.
- **Sửa:** bài của mình → MH-09 → thay đổi → lưu → quay lại nội dung đã cập nhật.
- **Xóa:** bài của mình → yêu cầu xóa → xác nhận → kết quả → về danh sách phù hợp.
- **Nhánh:** không phải chủ bài, bài không còn tồn tại, lưu/xóa lỗi, hủy.
- **Cần quyết:** ai có quyền, hậu quả với bài đã lưu/thông báo và cách cảnh báo thao tác mất dữ liệu.

### L-08 Thích lưu và tìm lại bài

- **Thích:** user tại MH-06/MH-07 → thích/bỏ thích → trạng thái và kết quả cập nhật.
- **Lưu:** bài → chọn nơi lưu → nhận kết quả → MH-12 → MH-13 → mở lại MH-07.
- **Nhánh:** guest cần xác thực, yêu cầu lỗi, bài bị xóa/ẩn, bộ sưu tập rỗng.
- **Cần quyết:** lưu nhanh hay chọn bộ sưu tập, bộ sưu tập mặc định, công khai/riêng tư và cách tránh trùng.

### L-09 Hồ sơ và theo dõi người dùng

- **Hồ sơ của mình:** MH-10 → MH-11 → sửa thông tin → lưu → quay về hồ sơ.
- **Theo dõi:** từ tác giả bài hoặc hồ sơ công khai → follow/unfollow → phản hồi kết quả.
- **Nhánh:** dữ liệu lỗi, hồ sơ không khả dụng, guest xác thực, request lỗi.
- **Cần quyết:** hồ sơ người khác có phải màn riêng, thông tin công khai, theo dõi có ảnh hưởng feed hay chỉ thông báo.

### L-10 Xem thông báo

- **Luồng:** MH-14 → xem danh sách → mở thông báo → nội dung liên quan → cập nhật đọc/chưa đọc theo quy tắc nhóm chốt.
- **Nhánh:** chưa có thông báo, nội dung đích bị xóa/ẩn, tải lỗi.
- **Cần quyết:** sự kiện tạo thông báo, có push ngoài ứng dụng không, cách đánh dấu đã đọc.

### L-11 Báo cáo bài có vấn đề

- **Luồng:** MH-07 → báo cáo → chọn lý do → gửi → nhận xác nhận tiếp nhận.
- **Nhánh:** guest cần xác thực nếu quy định; báo cáo trùng hoặc lỗi gửi.
- **Cần quyết:** đối tượng được báo cáo, quyền gửi, tiêu chí tự ẩn, khả năng xử lý báo cáo sai và trách nhiệm giải quyết.
- **Lưu ý:** không đưa màn admin vào danh sách. Xác nhận tiếp nhận không có nghĩa bài đã bị ẩn hoặc người báo cáo được thông báo mọi kết quả.

### L-12 Tìm kiếm và khám phá xu hướng

- **Luồng:** MH-15 → nhập món/khu vực và tiêu chí → xem kết quả → MH-07.
- **Xu hướng:** MH-16 hoặc vùng trong MH-15 → chọn mục → kết quả liên quan → MH-07.
- **Nhánh:** không có kết quả, tiêu chí quá hẹp, mạng lỗi.
- **Cần quyết:** phạm vi tìm món/quán/bài, tiêu chí lọc giá, cách nhập khu vực, định nghĩa xu hướng và ưu tiên nếu phải cắt scope.

### L-13 Tìm quán gần

- **Luồng đề xuất:** MH-17 → chọn dùng vị trí hoặc khu vực nhập → xem kết quả gần → mở thông tin/bài liên quan.
- **Nhánh:** từ chối quyền, thiết bị không có vị trí, ngoài khu vực dữ liệu mẫu, không có kết quả.
- **Cần quyết:** bản đồ/danh sách, bán kính mặc định 5 km theo mục tiêu Vision, đổi khu vực và cách ghi rõ vị trí dự phòng.
- **Nguyên tắc đề xuất:** không giả vờ vị trí mặc định là vị trí thật của người dùng.

### L-14 Quay món khi chưa có ý tưởng

- **Luồng:** từ màn chính → MH-18 → yêu cầu gợi ý → xem món → mở nội dung liên quan hoặc thử lại.
- **Nhánh:** thiếu dữ liệu phù hợp, request lỗi, thao tác lặp trong khi đang xử lý.
- **Cần quyết:** tiêu chí trước khi quay và thao tác nào được tính vào mục tiêu không quá hai thao tác của Vision. Animation chưa phải yêu cầu bắt buộc ở S1.

### L-15 Hỏi trợ lý và nhận bản nháp

- **Hỏi đáp:** MH-19 → gửi câu hỏi → chờ → xem trả lời và nội dung có trong hệ thống.
- **Draft:** yêu cầu soạn bài → xem draft → chọn dùng → MH-08 có dữ liệu gợi ý → người dùng rà soát/chỉnh → xác nhận đăng theo L-06.
- **Nhánh:** không tìm thấy dữ liệu, phản hồi chậm, AI không khả dụng, kết nối lỗi, draft thiếu thông tin.
- **Cần quyết:** quyền dùng chat, có lưu lịch sử không, dữ liệu draft và cơ chế lùi khi AI lỗi.
- **Nguyên tắc:** không tự đăng bài, không trình bày quán chưa kiểm chứng như dữ liệu thật, không đưa sinh ảnh vào phạm vi khi chưa được duyệt.

### L-16 Kết thúc phiên

- **Luồng:** user chọn đăng xuất → xác nhận nếu nhóm quy định → trở về trạng thái guest hoặc màn login.
- **Nhánh:** có nội dung đang nhập/chưa lưu; cần cảnh báo theo quy tắc chốt.
- **Cần quyết:** dữ liệu local nào giữ/xóa và ngữ cảnh trở về; chưa bổ sung multi-account.

## 5. Trạng thái UI cần đưa vào wireframe

| Nhóm | Trạng thái tối thiểu cần thiết kế |
|---|---|
| Đọc danh sách | Tải đầu, có dữ liệu, rỗng, tải thêm, hết dữ liệu, lỗi và thử lại |
| Đọc chi tiết | Loading, nội dung hợp lệ, ảnh lỗi, nội dung không còn khả dụng |
| Form | Chưa nhập, nhập sai, đang gửi, thành công, lỗi, nội dung chưa lưu |
| Thao tác cá nhân | Guest cần xác thực, đang xử lý, kết quả, lỗi, không đủ quyền |
| Vị trí | Chưa hỏi quyền, được phép, bị từ chối, không lấy được vị trí, khu vực dự phòng |
| AI | Chưa gửi, đang chờ, có kết quả, không có dữ liệu phù hợp, lỗi và khả năng thử lại |

Chưa yêu cầu dùng một framework hoặc cơ chế state cụ thể. FE bổ sung FR giao diện từ các trạng thái này ở WBS 2.1.2.

## 6. Những điểm cần quyết

| Vấn đề | Người đề xuất hoặc phối hợp | Người quyết đề xuất | Mốc |
|---|---|---|---|
| Quyền guest, login và đích quay lại | FE + BE | Lead cùng nhóm | Workshop S1 |
| Trường tài khoản và cách reset mật khẩu | BE, FE, trách nhiệm bảo mật | Lead cùng nhóm | Trước UC spec |
| Trường bài đăng; công thức; sửa/xóa; draft | FE + BE + DB | Lead cùng nhóm | Trước UC spec |
| Quyền quản lý và tính riêng tư bộ sưu tập | FE + BE + DB | Lead cùng nhóm | Trước FR và wireframe |
| Follow, notification và report | BE + FE; stakeholder liên quan | Lead cùng nhóm | Trước process flow |
| Tìm kiếm/xu hướng và thứ tự cắt phạm vi | FE + BE | Lead | MoSCoW S2 |
| Quyền vị trí và cách dùng fallback | FE + BE | Lead cùng nhóm | Trước wireframe |
| Phạm vi chat/draft, lịch sử và AI fallback | BE + FE + DB | Lead cùng nhóm | Trước đặc tả AI |
| Người review DOC WBS 1.1.1 | Lead | Lead | Khi giao task |

Đề xuất chốt trong tuần để đủ đầu vào họp 18/10. Nếu S2 được san sang tuần sau do quá tải, cập nhật mốc bằng quyết định nhóm, không tự thay lịch.

## 7 Chuyển giao và tiêu chí review

- Workshop 1.2.1: dùng actor và L-01 đến L-16 để thống nhất catalog UC; một luồng có thể tách/gộp UC theo mục tiêu người dùng.
- FE 1.2.2: ưu tiên đặc tả tài khoản, feed, bài đăng và hồ sơ. Tương tác/khám phá/AI do BE chủ trì phần UC theo WBS; FE cung cấp ngữ cảnh UI.
- FE 1.3.2: review process flow của BE bằng cách đối chiếu thao tác, kết quả và nhánh lỗi.
- FE 2.1.2: bổ sung FR phía giao diện từ trạng thái và hành vi cần có.
- FE 2.3.1: wireframe và navigation sau khi danh sách UC được gộp.
