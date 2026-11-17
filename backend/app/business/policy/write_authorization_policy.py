"""Kiểm quyền ghi tập trung cho bốn nhóm dịch vụ (SPEC S8 r2 §4, WP43-S8.3).

Policy là lớp **thuần**, không truy vấn: service nạp tài nguyên rồi truyền
`ResourceRef(resource_id, owner_id)`; nhờ vậy kiểm quyền nằm trong transaction của
service và test được không cần CSDL (CHI_TIET_LEAD 4.3 dòng 385).

Đầu ra là `None` hoặc `AuthorizationError` — không trả `bool`, để người gọi không
thể quên kiểm (dòng 404).
"""

from __future__ import annotations

from app._stubs.errors import UNAUTHENTICATED, AuthorizationError
from app._stubs.principal import Principal
from app.domain.enum.write_action import WriteAction
from app.domain.value.resource_ref import ResourceRef

#: Hành động chỉ cần có principal, không so chủ tài nguyên.
_PRINCIPAL_ONLY: frozenset[WriteAction] = frozenset(
    {
        WriteAction.CREATE_POST,
        WriteAction.LIKE,
        WriteAction.FOLLOW,
        WriteAction.REPORT,
    }
)


class WriteAuthorizationPolicy:
    """Singleton không trạng thái; khởi tạo bằng constructor rỗng."""

    __slots__ = ()

    def authorize_write(
        self,
        principal: Principal | None,
        action: WriteAction,
        resource: ResourceRef | None = None,
    ) -> None:
        """Cho qua hoặc ném `AuthorizationError` theo bảng kiểm CHI_TIET_LEAD dòng 394–402.

        `resource.owner_id is None` **không** được coi là chủ: hành động cần chủ sẽ
        nhận `FORBIDDEN`, không so `None == None` (dòng 389, 426).
        """
        if principal is None:
            raise AuthorizationError(
                "Cần đăng nhập để thực hiện thao tác này.",
                code=UNAUTHENTICATED,
            )

        if action in _PRINCIPAL_ONLY:
            return

        if action is WriteAction.SAVE:
            # SAVE là "lưu bài vào bộ sưu tập": người không phải chủ bài vẫn lưu
            # được, nhưng bộ sưu tập đích phải của chính họ.
            self.assert_owner(principal, _owner_of(resource), "bộ sưu tập")
            return

        labels = {
            WriteAction.UPDATE_POST: "bài viết",
            WriteAction.DELETE_POST: "bài viết",
            WriteAction.UPDATE_PROFILE: "hồ sơ",
            WriteAction.SET_VISIBILITY: "hồ sơ",
            WriteAction.COLLECTION: "bộ sưu tập",
            WriteAction.NOTIFICATION: "thông báo",
            WriteAction.ASSISTANT: "phiên trợ lý",
        }
        label = labels.get(action, "tài nguyên")
        self.assert_owner(principal, _owner_of(resource), label)

    def assert_owner(
        self,
        principal: Principal | None,
        owner_id: int | None,
        resource: str,
    ) -> None:
        """Dạng rút gọn cho tài nguyên một chủ (bài, bộ sưu tập, thông báo, phiên)."""
        if principal is None:
            raise AuthorizationError(
                "Cần đăng nhập để thực hiện thao tác này.",
                code=UNAUTHENTICATED,
            )
        if owner_id is None or owner_id != principal.user_id:
            raise AuthorizationError(f"Bạn không phải chủ {resource} này.")


def _owner_of(resource: ResourceRef | None) -> int | None:
    """Chủ của tài nguyên, hoặc `None` khi service không truyền tài nguyên."""
    return None if resource is None else resource.owner_id
