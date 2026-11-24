"""TC-BE-0106, 0306, 0207/0208: password, OTP and session crypto."""

import secrets
from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from app._stubs.clock import FixedClock
from app._stubs.errors import AuthorizationError, ValidationError
from app.business.identity.config import IdentityConfig
from app.business.identity.otp_service import OtpService
from app.business.identity.password_policy import PasswordPolicy
from app.business.identity.session_token_service import SessionTokenService
from app.domain.identity.user import User
from app.main import app
from fastapi.testclient import TestClient


def account() -> User:
    return User(id=1, token_version=3, is_active=True)


@pytest.mark.parametrize("raw", ["12345", "x" * 73, "ế" * 25])
def test_tc_be_0106_reject_invalid_password(raw: str) -> None:
    with pytest.raises(ValidationError) as error:
        PasswordPolicy().hash(raw)
    assert error.value.code == "VALIDATION_FAILED"
    assert error.value.field_errors[0].code == "PASSWORD_INVALID"


@pytest.mark.parametrize("raw", ["123456", "x" * 72, "ế" * 24])
def test_tc_be_0106_password_boundaries(raw: str) -> None:
    PasswordPolicy().validate(raw)


def test_tc_be_0106_bcrypt_salted_cost12() -> None:
    policy = PasswordPolicy()
    raw = secrets.token_urlsafe(10)
    first, second = policy.hash(raw), policy.hash(raw)
    assert first != second
    assert first.startswith("$2b$12$")
    assert policy.verify(raw, first) and policy.verify(raw, second)
    assert not policy.verify(raw + "!", first)
    assert not policy.verify("x" * 73, first)
    assert not policy.verify(raw, "invalid-hash")


def test_tc_be_0306_otp_generation_and_leading_zero(identity_config: IdentityConfig) -> None:
    otp = OtpService(identity_config)
    for _ in range(1000):
        code = otp.generate()
        assert len(code) == 6 and code.isascii() and code.isdigit()
    with patch("app.business.identity.otp_service.secrets.randbelow", return_value=7):
        assert otp.generate() == "000007"


def test_tc_be_0306_salted_keyed_hash(identity_config: IdentityConfig) -> None:
    otp = OtpService(identity_config)
    code = "012345"
    first, second = otp.hash(code), otp.hash(code)
    assert first != second and code not in first
    assert otp.verify(code, first) and otp.verify(code, second)
    assert not otp.verify("012344", first)
    assert not otp.verify(code, "bad-format")
    assert not otp.verify("１２３４５６", first)
    other = OtpService(IdentityConfig(identity_config.jwt_secret, secrets.token_hex(32)))
    assert not other.verify(code, first)


def test_tc_be_0207_token_roundtrip(tokens: SessionTokenService, clock: FixedClock) -> None:
    token = tokens.issue(account())
    claims = tokens.parse(token.raw)
    assert (claims.subject, claims.jti, claims.version) == (1, token.jti, 3)
    assert claims.expires_at - claims.issued_at == timedelta(days=7)
    assert claims.issued_at == clock.now()
    assert len(token.raw.encode()) < 1024
    assert token.raw not in repr(token)


@pytest.mark.parametrize("missing", ["sub", "jti", "ver", "iat", "exp"])
def test_tc_be_0208_missing_claim(
    missing: str, identity_config: IdentityConfig, tokens: SessionTokenService
) -> None:
    payload = jwt.decode(tokens.issue(account()).raw, options={"verify_signature": False})
    del payload[missing]
    raw = jwt.encode(payload, identity_config.jwt_secret, algorithm="HS256")
    with pytest.raises(AuthorizationError, match="Phiên đăng nhập"):
        tokens.parse(raw)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ver", True),
        ("ver", -1),
        ("sub", "0"),
        ("sub", "1.5"),
        ("jti", "bad"),
        ("exp", "invalid"),
        ("iat", True),
    ],
)
def test_tc_be_0208_claim_types(
    name: str, value: object, identity_config: IdentityConfig, tokens: SessionTokenService
) -> None:
    payload = jwt.decode(tokens.issue(account()).raw, options={"verify_signature": False})
    payload[name] = value
    with pytest.raises(AuthorizationError):
        tokens.parse(jwt.encode(payload, identity_config.jwt_secret, algorithm="HS256"))


def test_tc_be_0208_tampered_wrong_key_and_algorithm(
    identity_config: IdentityConfig, tokens: SessionTokenService
) -> None:
    payload = jwt.decode(tokens.issue(account()).raw, options={"verify_signature": False})
    candidates = [
        jwt.encode(payload, secrets.token_hex(32), algorithm="HS256"),
        jwt.encode(payload, identity_config.jwt_secret, algorithm="HS384"),
        "invalid.token.value",
        "x" * 1024,
    ]
    for raw in candidates:
        with pytest.raises(AuthorizationError) as error:
            tokens.parse(raw)
        assert error.value.code == "UNAUTHENTICATED"
        assert error.value.field_errors == ()


def test_tc_be_0209_expiry_boundary(
    identity_config: IdentityConfig, tokens: SessionTokenService, clock: FixedClock
) -> None:
    raw = tokens.issue(account()).raw
    before = SessionTokenService(
        identity_config, FixedClock(clock.now() + timedelta(days=7, seconds=-1))
    )
    assert before.parse(raw).subject == 1
    expired = SessionTokenService(identity_config, FixedClock(clock.now() + timedelta(days=7)))
    with pytest.raises(AuthorizationError):
        expired.parse(raw)


def test_config_required_and_repr_safe(identity_config: IdentityConfig) -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        IdentityConfig.from_env({})
    with pytest.raises(ValueError, match="OTP_PEPPER"):
        IdentityConfig(identity_config.jwt_secret, "")
    with pytest.raises(ValueError, match="HS256"):
        IdentityConfig(identity_config.jwt_secret, identity_config.otp_pepper, "HS512")
    assert identity_config.jwt_secret not in repr(identity_config)
    assert identity_config.otp_pepper not in repr(identity_config)


def test_failures_do_not_expose_secret_values(
    identity_config: IdentityConfig, tokens: SessionTokenService, caplog: pytest.LogCaptureFixture
) -> None:
    raw = tokens.issue(account()).raw
    with pytest.raises(AuthorizationError) as error:
        tokens.parse(raw + "broken")
    output = str(error.value) + repr(error.value) + caplog.text
    assert raw not in output
    assert identity_config.jwt_secret not in output
    assert identity_config.otp_pepper not in output


def test_startup_rejects_missing_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("OTP_PEPPER", raising=False)
    with pytest.raises(ValueError, match="JWT_SECRET"), TestClient(app):
        pass


def test_startup_accepts_valid_config(
    identity_config: IdentityConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", identity_config.jwt_secret)
    monkeypatch.setenv("OTP_PEPPER", identity_config.otp_pepper)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert app.state.identity_config == identity_config
