"""WP41-S8.4 handoff fake. Production always uses IdentityService."""

from uuid import UUID

from app.business.identity.session_token_service import unauthenticated
from app.domain.value.principal import Principal


class FakeSessionVerifier:
    def verify_session(self, raw_token: str) -> Principal:
        if raw_token != "test-1":  # noqa: S105 - public handoff fixture, not a credential
            raise unauthenticated()
        return Principal(1, UUID("00000000-0000-4000-8000-000000000001"), 0)
