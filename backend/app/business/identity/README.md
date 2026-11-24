# Nền Identity và Recovery nhóm 4.1

Phần S8 cung cấp dữ liệu tài khoản, các helper bảo mật và cổng xác thực dùng chung. API đăng ký, đăng nhập, đăng xuất và khôi phục được nối vào các phần này ở mốc S9–S10.

## Thành phần và trách nhiệm

| Thành phần | Trách nhiệm |
|---|---|
| `app/domain/identity/` | Bốn entity `User`, `PasswordReset`, `RevokedToken`, `UserDevice`, tương ứng T01–T04 |
| `app/dataaccess/identity/` | Bốn repository đọc/ghi bằng session của request; không tự commit |
| `PasswordPolicy` | Mật khẩu tối thiểu 6 ký tự, tối đa 72 byte UTF-8; bcrypt cost 12 |
| `OtpService` | Sinh 6 chữ số bằng `secrets`; lưu HMAC-SHA256 với salt và `OTP_PEPPER`; so sánh bằng `compare_digest` |
| `SessionTokenService` | Ký/đọc JWT HS256, hạn 7 ngày, chỉ gồm `sub`, `jti`, `ver`, `iat`, `exp` |
| `IdentityService` | Kiểm tra thu hồi, phiên bản và trạng thái tài khoản sau khi token đã qua kiểm chữ ký/thời hạn |
| `ContextFactory` | Đọc Bearer header một lần, gọi verifier rồi gắn `Principal` vào context của request |
| `require_principal` | Chặn resolver yêu cầu đăng nhập khi context là khách |

`Principal` được định nghĩa tại `app/domain/value/principal.py`, gồm `user_id: int`, `jti: UUID`, `version: int`. Đường import cũ `app._stubs.principal` trỏ tới cùng lớp để policy Social tiếp tục dùng được.

## Luồng kiểm phiên

1. Không có header: `ContextFactory` tạo context khách. Truy vấn công khai vẫn được thực hiện.
2. Có header nhưng sai dạng Bearer: trả `UNAUTHENTICATED`.
3. `SessionTokenService.parse` kiểm chữ ký HS256, đủ và đúng kiểu claims, hạn dùng theo UTC. Token lỗi bị từ chối trước khi truy vấn CSDL.
4. `SessionRepository.is_revoked` tra `jti` trong T03. Nếu đã thu hồi thì dừng.
5. `AccountRepository.find_by_id` đọc T01. Từ chối tài khoản không tồn tại, `token_version` lệch hoặc `is_active=false`.
6. Trả `Principal` cho resolver. Service nghiệp vụ tiếp tục kiểm quyền trên tài nguyên cụ thể qua policy.

Một token hợp lệ cần hai SELECT: T03 rồi T01. Không cache kết quả giữa các request. Không có refresh token.

`IdentityService.revoke_session(raw_token)` kiểm chữ ký và hạn, sau đó ghi T03 bằng `ON CONFLICT DO NOTHING`. Hàm không đi qua kiểm tra “chưa thu hồi”, vì cùng token được phép gọi thu hồi lặp. Resolver logout cần giữ đường đi này khi tích hợp.

## Dữ liệu và giao dịch

Schema lấy từ DOC 6.4-B. ORM không dùng `create_all` để thay migration. Test trích nguyên văn DDL vào CSDL kiểm thử riêng.

- T01: email chuẩn hóa là duy nhất. `update_password` chỉ đổi hash; luồng đặt lại phải gọi thêm `bump_token_version` trong cùng giao dịch với tiêu thụ grant.
- T02: partial UNIQUE cho phép tối đa một yêu cầu mở trên một tài khoản. `find_latest_by_email(..., for_update=True)` khóa đúng dòng yêu cầu; service khôi phục khóa tài khoản trước rồi mới khóa yêu cầu. `consume` cập nhật có điều kiện để một grant không thể được dùng hai lần.
- T03: `jti` là UUID; thu hồi lặp không tạo thêm dòng. `prune(now)` xóa token đã hết hạn.
- T04: `push_token` là duy nhất; platform chỉ nhận `android` hoặc `web`. Xóa thiết bị phải khớp cả chủ sở hữu và token. Quyết định cung cấp API thiết bị thuộc phạm vi chức năng đã được duyệt.

Repository chỉ flush/thực hiện câu SQL. Service và TransactionManager chịu trách nhiệm commit/rollback toàn bộ use case. Lỗi ràng buộc đi qua mapper lỗi chung ở ranh giới API.

## Kết nối với request scope của API

```python
from app.bootstrap.identity_scope import build_identity_service

# Dùng đúng Session đang thuộc request, không tạo một Session ẩn trong service.
scope.session_verifier = build_identity_service(session, identity_config, clock)
context = ContextFactory(clock).build(request, scope)
principal = require_principal(context)
```

`ContextFactory` và `require_principal` ở `app/presentation/graphql/context.py`. Scope cần cung cấp thuộc tính `session_verifier` có phương thức `verify_session(raw_token: str) -> Principal`. Context factory chỉ xác thực; ErrorMapper chung chuyển ngoại lệ miền thành lỗi API đúng hợp đồng. Resolver không tự giải mã JWT.

Fake bàn giao ở `tests/fakes/fake_session_verifier.py` chỉ nhận `test-1`. Fake nằm trong test; bootstrap thật luôn tạo `IdentityService`.

## Cấu hình và chạy

Python 3.12. Đặt `JWT_SECRET` tối thiểu 32 byte và `OTP_PEPPER` riêng trong môi trường hoặc `.env` không được commit. `JWT_ALGORITHM=HS256`, `JWT_TTL_DAYS=7`. Thiếu hoặc sai cấu hình, FastAPI dừng lúc startup. Có thể sinh mỗi giá trị bằng `python -c "import secrets; print(secrets.token_urlsafe(32))"` rồi lưu riêng trong `.env`.

Từ `backend/`:

```powershell
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --env-file ../.env
```

Trước khi kiểm thử, `DATABASE_URL_TEST` phải trỏ tới **CSDL PostgreSQL riêng dành cho test**. Fixture dựng lại các bảng của bộ test, mỗi ca chạy trong giao dịch rollback. Không dùng CSDL đang có dữ liệu ứng dụng.

```powershell
ruff check app tests
ruff format --check app tests
mypy app tests
pytest tests/identity -q
pytest -q
```

Các ca Identity gồm ràng buộc PostgreSQL thật, khóa dòng bằng hai connection, grant dùng một lần, bcrypt/OTP/JWT, thứ tự kiểm phiên, số SELECT và mutation GraphQL kiểm quyền đăng nhập. Mutation `identityProbe` chỉ có trong test; không mở operation thử nghiệm trên API sản phẩm.

## Tài liệu thiết kế

- `docs/quan_ly/huong_dan_s8_s11/CHI_TIET_FE_4.1_IDENTITY.md`, mục 6.1.
- DOC 6.1-A BE: lớp Identity, repository D1 và các value object.
- DOC 6.4-B: DDL T01–T04 và chỉ mục.
- DOC 5.4-A: JWT, mật khẩu, OTP và thu hồi phiên.
