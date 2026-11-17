"""Kiểm bản giả điểm nối (SPEC S8 r2 §3) và `Base` — không cần CSDL."""

from __future__ import annotations

import base64
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from typing import Final
from uuid import UUID, uuid4

import pytest
from app._stubs.clock import Clock, FixedClock
from app._stubs.db import make_engine, resolve_database_url
from app._stubs.errors import (
    UNAUTHENTICATED,
    VALIDATION_FAILED,
    AuthorizationError,
    BusinessRuleError,
    DomainError,
    FieldError,
    IntegrationError,
    NotFoundError,
    SystemError,
    ValidationError,
)
from app._stubs.pagination import CursorCodec, PageRequest
from app._stubs.principal import Principal, SessionClaims
from app._stubs.transaction import TransactionManager

INSTANT: Final = datetime(2026, 11, 17, 3, 4, 5, 123456, tzinfo=UTC)


class FakeSession:
    """Session giả ghi lại thứ tự commit/rollback."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def commit(self) -> None:
        self.events.append("commit")

    def rollback(self) -> None:
        self.events.append("rollback")


@pytest.mark.parametrize(
    ("error_class", "expected_code"),
    [
        (ValidationError, "VALIDATION_FAILED"),
        (BusinessRuleError, "CONFLICT"),
        (AuthorizationError, "FORBIDDEN"),
        (NotFoundError, "NOT_FOUND"),
        (IntegrationError, "INTEGRATION_UNAVAILABLE"),
        (SystemError, "INTERNAL_ERROR"),
    ],
)
def test_moi_lop_loi_mang_ma_hop_dong(error_class: type[DomainError], expected_code: str) -> None:
    error = error_class("Thông điệp an toàn")

    assert isinstance(error, DomainError)
    assert error.code == expected_code
    assert error.message == "Thông điệp an toàn"
    assert error.timestamp.tzinfo is not None


def test_authorization_error_doi_duoc_ma_va_giu_field_errors() -> None:
    field = FieldError(field="page.after", code="CURSOR_INVALID", message="Con trỏ sai")

    error = AuthorizationError("Thiếu token", code=UNAUTHENTICATED, field_errors=(field,))

    assert error.code == UNAUTHENTICATED
    assert error.field_errors == (field,)


def test_ma_loi_ngoai_hop_dong_bi_tu_choi() -> None:
    with pytest.raises(ValueError, match="không thuộc hợp đồng"):
        DomainError("x", code="SOMETHING_ELSE")


def test_page_request_default_va_gioi_han() -> None:
    default = PageRequest.default()
    assert default.first == 10
    assert default.after is None
    assert PageRequest.from_input(None).first == 10
    assert PageRequest.from_input(50).first == 50
    assert PageRequest.from_input(51).first == 50


@pytest.mark.parametrize("first", [0, -1])
def test_page_request_first_khong_duong_bi_tu_choi(first: int) -> None:
    with pytest.raises(ValidationError) as caught:
        PageRequest.from_input(first)

    assert caught.value.code == VALIDATION_FAILED
    assert caught.value.field_errors[0].code == "PAGE_SIZE_INVALID"


def test_page_request_khoi_tao_truc_tiep_kiem_1_den_50() -> None:
    with pytest.raises(ValidationError):
        PageRequest(first=0)
    with pytest.raises(ValidationError):
        PageRequest(first=51)


def test_cursor_khu_hoi_giu_created_at_va_id() -> None:
    cursor = CursorCodec.encode(INSTANT, 987654321)

    payload = CursorCodec.decode(cursor)

    assert payload.created_at == INSTANT
    assert payload.id == 987654321


def test_cursor_doi_mui_gio_ve_utc() -> None:
    local = INSTANT.astimezone(timezone(timedelta(hours=7)))

    payload = CursorCodec.decode(CursorCodec.encode(local, 5))

    assert payload.created_at == INSTANT
    assert payload.created_at.tzinfo == UTC


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        "not-a-cursor",
        base64.urlsafe_b64encode(b"khong-co-dau-phan-cach").decode(),
        base64.urlsafe_b64encode(b"2026-11-17T00:00:00+00:00|0").decode(),
        base64.urlsafe_b64encode(b"2026-11-17T00:00:00|12").decode(),
    ],
)
def test_cursor_sai_dinh_dang_bao_cursor_invalid(cursor: str) -> None:
    with pytest.raises(ValidationError) as caught:
        CursorCodec.decode(cursor)

    assert caught.value.code == VALIDATION_FAILED
    assert caught.value.field_errors[0].field == "page.after"
    assert caught.value.field_errors[0].code == "CURSOR_INVALID"


def test_transaction_manager_chay_after_commit_sau_commit() -> None:
    session = FakeSession()
    manager = TransactionManager(session)

    def work() -> int:
        session.events.append("work")
        manager.after_commit(lambda: session.events.append("after-commit"))
        return 42

    assert manager.run(work) == 42
    assert session.events == ["work", "commit", "after-commit"]


def test_transaction_manager_bo_after_commit_khi_rollback() -> None:
    session = FakeSession()
    manager = TransactionManager(session)

    def failing() -> None:
        session.events.append("work")
        manager.after_commit(lambda: session.events.append("after-commit"))
        raise RuntimeError("lỗi nghiệp vụ")

    with pytest.raises(RuntimeError):
        manager.run(failing)

    assert session.events == ["work", "rollback"]

    # Việc sau commit đã bị xóa: lượt sau thành công không chạy lại callback cũ.
    assert manager.run(lambda: "ok") == "ok"
    assert session.events == ["work", "rollback", "commit"]


def test_clock_tra_thoi_diem_utc_va_fixed_clock() -> None:
    assert Clock().now().tzinfo is not None
    assert FixedClock(INSTANT).now() == INSTANT
    assert FixedClock(INSTANT).today() == INSTANT.date()
    with pytest.raises(ValueError, match="múi giờ"):
        FixedClock(datetime(2026, 11, 17))


def test_principal_va_session_claims_bat_bien() -> None:
    jti = uuid4()
    principal = Principal(user_id=7, jti=jti, version=2)
    claims = SessionClaims(
        subject=7,
        jti=jti,
        version=2,
        issued_at=INSTANT,
        expires_at=INSTANT + timedelta(days=7),
    )

    assert principal.user_id == 7
    assert claims.expires_at - claims.issued_at == timedelta(days=7)
    with pytest.raises(FrozenInstanceError):
        setattr(principal, "version", 3)  # noqa: B010 - cố tình thử ghi vào frozen dataclass


def test_session_claims_jti_la_uuid() -> None:
    claims = SessionClaims(
        subject=1,
        jti=uuid4(),
        version=0,
        issued_at=INSTANT,
        expires_at=INSTANT,
    )

    assert isinstance(claims.jti, UUID)


def test_db_resolve_url_theo_bien_moi_truong(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL_TEST", "postgresql+psycopg://u:p@db:5432/tomateto_test")

    assert resolve_database_url() == "postgresql+psycopg://u:p@db:5432/tomateto_test"
    assert resolve_database_url("postgresql+psycopg://u:p@khac:5432/x").endswith("/x")


def test_db_make_engine_khong_ket_noi_ngay() -> None:
    engine = make_engine("postgresql+psycopg://u:p@localhost:5433/tomateto_test")
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.url.database == "tomateto_test"
    finally:
        engine.dispose()
