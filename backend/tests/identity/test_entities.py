"""OTP and grant state boundaries; checks use an injected UTC instant."""

from datetime import timedelta

import pytest
from app._stubs.clock import FixedClock
from app.domain.identity.password_reset import PasswordReset


def test_fifth_wrong_otp_invalidates_request(clock: FixedClock) -> None:
    request = PasswordReset(failed_attempts=0, otp_expires_at=clock.now() + timedelta(minutes=10))
    assert request.is_otp_valid(clock.now())
    for _ in range(4):
        request.register_failed_attempt(clock.now())
        assert request.is_otp_valid(clock.now())
    request.register_failed_attempt(clock.now())
    assert not request.is_otp_valid(clock.now())
    assert request.failed_attempts == 5 and request.invalidated_at == clock.now()
    request.register_failed_attempt(clock.now())
    assert request.failed_attempts == 5


def test_otp_expiry_and_verification_end_otp_stage(clock: FixedClock) -> None:
    request = PasswordReset(failed_attempts=0, otp_expires_at=clock.now())
    assert not request.is_otp_valid(clock.now())
    request.otp_expires_at = clock.now() + timedelta(minutes=10)
    request.verified_at = clock.now()
    assert not request.is_otp_valid(clock.now())


def test_grant_cannot_be_reused_or_consumed_before_verify(clock: FixedClock) -> None:
    request = PasswordReset()
    with pytest.raises(ValueError):
        request.consume(clock.now())
    request.verified_at = clock.now()
    request.reset_expires_at = clock.now() + timedelta(minutes=15)
    request.consume(clock.now())
    assert request.consumed_at == clock.now()
    with pytest.raises(ValueError):
        request.consume(clock.now())


def test_grant_expiry_boundary(clock: FixedClock) -> None:
    request = PasswordReset(verified_at=clock.now(), reset_expires_at=clock.now())
    with pytest.raises(ValueError):
        request.consume(clock.now())
