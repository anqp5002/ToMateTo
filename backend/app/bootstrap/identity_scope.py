"""Construct the Identity service with the caller's request-owned session."""

from sqlalchemy.orm import Session

from app._stubs.clock import Clock
from app.business.identity.config import IdentityConfig
from app.business.identity.identity_service import IdentityService
from app.business.identity.session_token_service import SessionTokenService
from app.dataaccess.identity.account_repository import AccountRepository
from app.dataaccess.identity.session_repository import SessionRepository


def build_identity_service(
    session: Session, config: IdentityConfig, clock: Clock
) -> IdentityService:
    return IdentityService(
        AccountRepository(session), SessionRepository(session), SessionTokenService(config, clock)
    )
