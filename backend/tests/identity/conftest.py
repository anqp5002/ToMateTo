import secrets
from datetime import UTC, datetime

import pytest
from app._stubs.clock import FixedClock
from app.business.identity.config import IdentityConfig
from app.business.identity.session_token_service import SessionTokenService


@pytest.fixture
def identity_config() -> IdentityConfig:
    return IdentityConfig(jwt_secret=secrets.token_hex(32), otp_pepper=secrets.token_hex(32))


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 11, 24, 12, tzinfo=UTC))


@pytest.fixture
def tokens(identity_config: IdentityConfig, clock: FixedClock) -> SessionTokenService:
    return SessionTokenService(identity_config, clock)
