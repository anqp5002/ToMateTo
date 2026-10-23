# S1 Actor Use Case và quyết định nghiệp vụ

> Dự án: ToMateTo  
> WBS: 1.2.1 — Chốt actor và danh sách Use Case  
> Owner đề xuất: Lead điều phối, cả nhóm tham gia  
> Người tổng hợp: FE | Reviewer: Cần nhóm chỉ định
> Sprint: S1 


## 1. Mục đích và giới hạn
Tài liệu xác định actor, các quyết định nghiệp vụ và danh sách Use Case của ToMateTo, làm cơ sở xây dựng đặc tả trong S1.
Danh sách màn hình được quản lý trong tài liệu WBS 1.1.1. Việc bố trí thao tác quản lý bài, gỡ đề cập và tùy chỉnh quyền riêng tư sẽ được xác định tại bước wireframe. Một Use Case có thể liên quan đến nhiều màn hình, và một màn hình có thể phục vụ nhiều Use Case.
Danh sách Use Case và phân công đặc tả được trình nhóm review trước khi phê duyệt.

## 2. Quyết định nghiệp vụ thống nhất

| ID | Nội dung quyết định | Hệ quả đối với đặc tả |
|---|---|---|
| QD-01 | Khách được xem feed, chi tiết bài và tìm kiếm. Đăng bài, thích, lưu và theo dõi yêu cầu đăng nhập. | Có luồng xem không cần tài khoản và nhánh yêu cầu xác thực trước thao tác cá nhân. Quyền khách với các chức năng khám phá khác cần cả nhóm chốt. |
| QD-02 | Sau đăng nhập từ một thao tác bị yêu cầu xác thực, quay về ngữ cảnh trước đó; không tự thực hiện thao tác. | Người dùng bấm lại để thực hiện; hủy đăng nhập không làm phát sinh thao tác. |
| QD-03 | Đăng ký thành công tự đăng nhập và về feed. | Tạo tài khoản thành công dẫn tới phiên đăng nhập; không mặc định thêm onboarding. |
| QD-04 | Khôi phục mật khẩu bằng OTP gửi qua email. | Đặc tả yêu cầu OTP, xác minh và đặt mật khẩu mới; khả năng gửi email cần BE xác nhận. |
| QD-05 | Bài đăng bắt buộc có tên món. Ảnh có hoặc không tùy người đăng; quán, giá, địa chỉ và cảm nhận đều tùy chọn. | Bài chỉ có tên món vẫn hợp lệ. Không đặt thêm điều kiện phải có ảnh, địa điểm hoặc cảm nhận. Nếu có dữ liệu tùy chọn, vẫn kiểm tra định dạng và giới hạn được nhóm chốt. |
| QD-06 | Chủ bài và admin có quyền sửa/xóa bài. Người được đề cập có quyền không xuất hiện trong bài đó. | Phân biệt quyền sửa/xóa toàn bài với quyền gỡ đề cập của chính mình. Các điều kiện admin và phạm vi đề cập cần đặc tả tiếp. |
| QD-07 | Người dùng được chọn thông tin hồ sơ nào công khai. Email không công khai. | Email không nằm trong tùy chọn cho phép công khai. Danh sách trường và mức hiển thị mặc định cần chốt. |
| QD-08 | Có bộ sưu tập mặc định “Đã lưu”; người dùng có thể tạo nhóm riêng. | Đặc tả lưu nhanh và quản lý bộ sưu tập; quy tắc đổi tên/xóa/chuyển bài cần chốt thêm. |
| QD-09 | Theo dõi chưa làm thay đổi feed trong phiên bản đầu. Feed có mới nhất và đang hot. | Không thêm feed chỉ gồm tác giả đang theo dõi; định nghĩa đang hot sẽ được nhóm xác định. |
| QD-10 | Một báo cáo không làm bài tự ẩn ngay; tiêu chí tự ẩn cần chốt riêng. | Gửi báo cáo và quyết định xử lý nội dung là hai bước khác nhau; chưa đặt ngưỡng số báo cáo. |

### 2.1 Cách diễn giải quyền gỡ đề cập
Để soạn UC, đề xuất hiểu “không hiện ở bài viết đó” là người được đề cập có thể gỡ sự liên kết/đề cập tới chính mình khỏi bài. Quyền này không bao gồm sửa nội dung khác hoặc xóa toàn bộ bài của tác giả.
Đây là cách diễn giải cần xác nhận trong đặc tả: đề cập bằng tài khoản khác với tên viết trong văn bản hoặc hình ảnh có người xuất hiện. Chưa mặc định hệ thống tự nhận diện người trong ảnh, xóa ảnh hoặc kiểm soát mọi lần tác giả viết tên.

## 3. Actor

| ID | Actor | Vai trò và quyền chính |
|---|---|---|
| A-01 | Khách chưa đăng nhập | Xem các nội dung được phép công khai, đăng ký, đăng nhập và bắt đầu khôi phục mật khẩu. |
| A-02 | Người dùng đã đăng nhập | Đăng bài, tương tác cá nhân, lưu nội dung, quản lý hồ sơ và sử dụng các chức năng được phân quyền. |
| A-03 | Admin | Sửa/xóa bài theo quyền được cấp. Chưa mở rộng thành quyền đọc dữ liệu riêng tư, thay đổi tài khoản hoặc quản trị mọi chức năng. |

Ngữ cảnh của A-02:
- **Chủ bài:** người dùng sở hữu bài, có quyền sửa/xóa bài đó.
- **Người được đề cập:** người dùng được đề cập trong bài, có quyền gỡ đề cập tới mình theo QD-06.
- **Chủ hồ sơ:** người dùng quản lý hồ sơ của mình và lựa chọn thông tin công khai.
  
Các ngữ cảnh trên không phải ba loại tài khoản riêng. Một người có thể đồng thời là chủ bài, người được đề cập và chủ hồ sơ. Admin không mặc nhiên được công khai email hoặc xem thông tin riêng tư chỉ vì có quyền xử lý bài.

## 4. Catalog Use Case đề xuất

Mỗi Use Case được gán một mã định danh để truy vết giữa yêu cầu, đặc tả và thiết kế. Nhóm thống nhất danh sách và mã UC trước khi viết đặc tả chi tiết.

| ID | Use Case | Actor khởi tạo | Kết quả mong muốn | Đề xuất chủ trì đặc tả |
|---|---|---|---|---|
| UC-01 | Đăng ký tài khoản | Khách | Có tài khoản, phiên đăng nhập và được đưa về feed | FE |
| UC-02 | Đăng nhập | Khách | Có phiên xác thực; trở về ngữ cảnh yêu cầu nếu có | FE |
| UC-03 | Khôi phục mật khẩu | Khách | Xác minh OTP email và đặt mật khẩu mới | FE, phối hợp BE |
| UC-04 | Đăng xuất | User | Kết thúc phiên hiện tại | FE |
| UC-05 | Xem feed | Khách, User | Xem bài mới nhất hoặc đang hot | FE |
| UC-06 | Xem chi tiết bài | Khách, User | Xem nội dung bài đang được phép truy cập | FE |
| UC-07 | Tạo bài đăng | User | Tạo bài có tên món; thông tin còn lại tùy chọn | FE |
| UC-08 | Sửa bài của mình | User là chủ bài | Nội dung bài được cập nhật | FE |
| UC-09 | Xóa bài của mình | User là chủ bài | Bài được xóa theo quy tắc xác nhận | FE |
| UC-10 | Thích hoặc bỏ thích bài | User | Trạng thái thích được cập nhật | BE, FE góp luồng giao diện |
| UC-11 | Lưu hoặc bỏ lưu bài | User | Bài được lưu hoặc bỏ khỏi phạm vi lưu đã chốt | BE, FE góp luồng giao diện |
| UC-12 | Tạo và quản lý bộ sưu tập | User | Tổ chức nội dung đã lưu | BE; thao tác cụ thể cần chốt |
| UC-13 | Theo dõi hoặc bỏ theo dõi | User | Quan hệ theo dõi được cập nhật, không đổi feed | BE |
| UC-14 | Xem hồ sơ | User; Khách nếu được duyệt | Xem thông tin theo quyền công khai | FE |
| UC-15 | Cập nhật hồ sơ của mình | User là chủ hồ sơ | Thông tin hồ sơ được cập nhật | FE |
| UC-16 | Tùy chỉnh công khai hồ sơ | User là chủ hồ sơ | Thông tin hiển thị đúng lựa chọn; email không công khai | FE, phối hợp BE |
| UC-17 | Xem và đánh dấu thông báo | User | Biết sự kiện liên quan và trạng thái đã đọc | BE |
| UC-18 | Báo cáo bài | User | Báo cáo được tiếp nhận; không mặc định ẩn bài ngay | BE |
| UC-19 | Sửa bài với quyền admin | Admin | Bài được chỉnh theo quyền và quy tắc xử lý | BE, FE góp thao tác |
| UC-20 | Xóa bài với quyền admin | Admin | Bài được xóa theo quyền và quy tắc xử lý | BE, FE góp thao tác |
| UC-21 | Gỡ đề cập tới bản thân | User được đề cập | Bản thân không còn xuất hiện dưới dạng đề cập được hệ thống quản lý | FE + BE; cần xác nhận cách hiểu |
| UC-22 | Tìm kiếm món quán hoặc bài | Khách, User | Có kết quả theo phạm vi tìm kiếm được chốt | BE |
| UC-23 | Xem xu hướng | Actor cần chốt | Xem các mục nổi bật theo tiêu chí nhóm chọn | BE |
| UC-24 | Tìm quán gần | Actor cần chốt | Có kết quả quanh vị trí hoặc khu vực dự phòng | BE, FE góp luồng quyền vị trí |
| UC-25 | Nhận gợi ý quay món | Actor cần chốt | Có gợi ý và thông tin liên quan | BE |
| UC-26 | Hỏi trợ lý | Actor cần chốt | Nhận câu trả lời dựa trên dữ liệu hệ thống hoặc thông báo không khả dụng | BE |
| UC-27 | Nhận và sử dụng bài nháp của trợ lý | Actor cần chốt | Nhận draft, rà soát và chuyển sang tạo bài; không tự đăng | BE + FE |

UC-12 có thể tách thành tạo, đổi tên, xóa và xem bộ sưu tập nếu các mục tiêu này được duyệt. UC-03 có thể chia chi tiết theo bước OTP nhưng không bắt buộc mỗi bước là một UC. UC-21 cần có cơ chế đề cập được nhóm chọn; việc tạo đề cập sẽ được mô tả trong tạo/sửa bài hoặc tách UC nếu workshop quyết định.
