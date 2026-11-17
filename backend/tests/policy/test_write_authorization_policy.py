"""Test chính sách quyền ghi (SPEC S8 r2 §4, WP43-S8.3) — không cần CSDL."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest
from app._stubs.errors import UNAUTHENTICATED, AuthorizationError
from app._stubs.principal import Principal
from app.business.policy.write_authorization_policy import WriteAuthorizationPolicy
from app.domain.enum.write_action import WriteAction
from app.domain.value.resource_ref import ResourceRef

OWNER_ID = 7
OTHER_ID = 99

#: Hành động đòi `resource.owner_id == principal.user_id`.
OWNER_REQUIRED: tuple[WriteAction, ...] = (
    WriteAction.UPDATE_POST,
    WriteAction.DELETE_POST,
    WriteAction.UPDATE_PROFILE,
    WriteAction.SET_VISIBILITY,
    WriteAction.SAVE,
    WriteAction.COLLECTION,
    WriteAction.NOTIFICATION,
    WriteAction.ASSISTANT,
)

#: Hành động chỉ cần đã đăng nhập; người không phải chủ vẫn được phép.
PRINCIPAL_ONLY: tuple[WriteAction, ...] = (
    WriteAction.CREATE_POST,
    WriteAction.LIKE,
    WriteAction.FOLLOW,
    WriteAction.REPORT,
)

POLICY = WriteAuthorizationPolicy()


def make_principal(user_id: int = OWNER_ID) -> Principal:
    return Principal(user_id=user_id, jti=uuid4(), version=1)


def make_resource(owner_id: int | None = OWNER_ID) -> ResourceRef:
    return ResourceRef(resource_id=42, owner_id=owner_id)


def _write_attribute(target: object, attribute: str, value: object) -> None:
    """Ghi thuộc tính bằng tên động — để kiểm dataclass frozen mà mypy không chặn."""
    setattr(target, attribute, value)


def test_co_du_muoi_hai_write_action() -> None:
    assert len(WriteAction) == 12
    assert {item.value for item in WriteAction} == {
        "CREATE_POST",
        "UPDATE_POST",
        "DELETE_POST",
        "UPDATE_PROFILE",
        "SET_VISIBILITY",
        "LIKE",
        "SAVE",
        "REPORT",
        "FOLLOW",
        "COLLECTION",
        "NOTIFICATION",
        "ASSISTANT",
    }


@pytest.mark.parametrize("action", list(WriteAction), ids=lambda item: item.value)
def test_khong_principal_luon_unauthenticated(action: WriteAction) -> None:
    """TC-BE-N0701 nhánh 1: mọi hành động ghi đều cần đăng nhập."""
    with pytest.raises(AuthorizationError) as caught:
        POLICY.authorize_write(None, action, make_resource())

    error = caught.value
    assert error.code == UNAUTHENTICATED
    assert error.field_errors == ()
    assert error.message


@pytest.mark.parametrize("action", OWNER_REQUIRED, ids=lambda item: item.value)
def test_nguoi_khong_phai_chu_bi_forbidden(action: WriteAction) -> None:
    """TC-BE-N0701 nhánh 2: đã đăng nhập nhưng không phải chủ → FORBIDDEN."""
    with pytest.raises(AuthorizationError) as caught:
        POLICY.authorize_write(make_principal(OTHER_ID), action, make_resource(OWNER_ID))

    error = caught.value
    assert error.code == "FORBIDDEN"
    assert error.field_errors == ()
    assert error.message


@pytest.mark.parametrize("action", PRINCIPAL_ONLY, ids=lambda item: item.value)
def test_nguoi_khong_phai_chu_van_duoc_like_follow_report_tao_bai(
    action: WriteAction,
) -> None:
    """LIKE/FOLLOW/REPORT (và tạo bài) không đòi quyền chủ tài nguyên đích."""
    POLICY.authorize_write(make_principal(OTHER_ID), action, make_resource(OWNER_ID))

    # Không cần resource cũng không ném: các hành động này không đọc owner.
    POLICY.authorize_write(make_principal(OTHER_ID), action, None)


@pytest.mark.parametrize("action", list(WriteAction), ids=lambda item: item.value)
def test_dung_chu_thi_di_qua(action: WriteAction) -> None:
    """TC-BE-N0701 nhánh 3: đúng chủ thì không ném."""
    POLICY.authorize_write(make_principal(OWNER_ID), action, make_resource(OWNER_ID))


@pytest.mark.parametrize("action", OWNER_REQUIRED, ids=lambda item: item.value)
def test_owner_id_none_khong_duoc_coi_la_chu(action: WriteAction) -> None:
    """Ca biên dòng 417/426: null ≠ null, phải FORBIDDEN."""
    with pytest.raises(AuthorizationError) as caught:
        POLICY.authorize_write(make_principal(), action, make_resource(owner_id=None))

    assert caught.value.code == "FORBIDDEN"


@pytest.mark.parametrize("action", OWNER_REQUIRED, ids=lambda item: item.value)
def test_thieu_resource_cung_bi_forbidden(action: WriteAction) -> None:
    """Service quên nạp tài nguyên → từ chối, không mặc định cho qua."""
    with pytest.raises(AuthorizationError) as caught:
        POLICY.authorize_write(make_principal(), action)

    assert caught.value.code == "FORBIDDEN"


def test_service_nap_nham_owner_id_kieu_sai_thi_khong_coi_la_chu() -> None:
    """Chủ tài nguyên khác principal, dù principal có id trùng "rỗng" cũng không qua."""
    with pytest.raises(AuthorizationError):
        POLICY.authorize_write(make_principal(1), WriteAction.UPDATE_POST, make_resource(2))


@pytest.mark.parametrize(
    ("principal", "owner_id", "expected_code"),
    [
        (None, OWNER_ID, UNAUTHENTICATED),
        (make_principal(OTHER_ID), None, "FORBIDDEN"),
        (make_principal(OTHER_ID), OWNER_ID, "FORBIDDEN"),
        (make_principal(OWNER_ID), None, "FORBIDDEN"),
        (make_principal(OWNER_ID), OWNER_ID, None),
    ],
    ids=[
        "thieu-principal",
        "owner-null",
        "khac-chu",
        "principal-la-chu-nhung-owner-null",
        "dung-chu",
    ],
)
def test_assert_owner_cac_nhanh(
    principal: Principal | None, owner_id: int | None, expected_code: str | None
) -> None:
    if expected_code is None:
        POLICY.assert_owner(principal, owner_id, "bài viết")
        return

    with pytest.raises(AuthorizationError) as caught:
        POLICY.assert_owner(principal, owner_id, "bài viết")

    assert caught.value.code == expected_code
    assert caught.value.field_errors == ()


def test_policy_khong_trang_thai_va_dung_lai_duoc() -> None:
    first = WriteAuthorizationPolicy()
    second = WriteAuthorizationPolicy()

    first.authorize_write(make_principal(), WriteAction.CREATE_POST, None)
    second.authorize_write(make_principal(), WriteAction.CREATE_POST, None)

    assert first.__slots__ == ()
    assert not hasattr(first, "__dict__")


def test_resource_ref_bat_bien_va_chan_id_khong_duong() -> None:
    resource = ResourceRef(resource_id=1, owner_id=None)

    assert resource.owner_id is None
    with pytest.raises(FrozenInstanceError):
        _write_attribute(resource, "owner_id", OWNER_ID)
    with pytest.raises(ValueError, match="owner_id"):
        ResourceRef(owner_id=0)
    with pytest.raises(ValueError, match="resource_id"):
        ResourceRef(resource_id=-1)
