# ToMateTo

Ứng dụng cộng đồng chia sẻ món ăn và quán ngon, giúp người dùng quyết định "hôm nay ăn gì" nhanh hơn.

Dự án do nhóm 4 người (Lead, FE, BE, DB) thực hiện theo từng sprint, từ phân tích yêu cầu, thiết kế đến cài đặt.

## Cách làm việc

- Mỗi tuần làm 2 sprint; họp trực tiếp 1 lần vào Chủ nhật.
- Trong tuần: mỗi thành viên làm task của mình, đẩy lên nhánh riêng và tạo Pull Request; reviewer chéo review và yêu cầu sửa nếu cần.
- Chủ nhật: báo cáo, hỏi đáp, reviewer đánh giá lại rồi merge vào `main`.
- Không commit trực tiếp vào `main`; mọi thay đổi đi qua Pull Request.

## Quy ước nhánh và commit

- Nhánh: `feat|fix|docs|chore/<scope>-<mô-tả>`, scope gồm `fe`, `be`, `db`, `infra`, `docs`.
- Commit: `<type>(<scope>): <mô tả>`, ghi rõ sprint trong phần mô tả.
- Không đưa khóa, mật khẩu hoặc file `.env` thật lên repo.

## Cấu trúc tài liệu

Tài liệu từng sprint nằm trong thư mục `docs/`, được thêm vào qua Pull Request của từng thành viên.
