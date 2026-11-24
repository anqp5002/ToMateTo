"""Verify the resolver boundary with the real Identity service and PostgreSQL."""

import secrets
from dataclasses import dataclass

import strawberry
from app._stubs.clock import FixedClock
from app._stubs.errors import AuthorizationError
from app.bootstrap.identity_scope import build_identity_service
from app.business.identity.config import IdentityConfig
from app.business.identity.session_token_service import SessionTokenService
from app.dataaccess.identity.account_repository import AccountRepository
from app.domain.identity.user import User
from app.presentation.graphql.context import (
    ContextFactory,
    RequestContext,
    SessionVerifier,
    require_principal,
)
from graphql import GraphQLError
from sqlalchemy.orm import Session
from starlette.requests import Request
from strawberry.types import Info


@dataclass
class Scope:
    session_verifier: SessionVerifier


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> bool:
        return True


@strawberry.type
class Mutation:
    @strawberry.mutation
    def identity_probe(self, info: Info[RequestContext, None]) -> int:
        # Probe is test-only. The production ErrorMapper remains owned by BE.
        try:
            return require_principal(info.context).user_id
        except AuthorizationError as error:
            raise GraphQLError(error.message, extensions={"code": error.code}) from None


def test_guarded_mutation_real_service(
    db_session: Session, identity_config: IdentityConfig, clock: FixedClock
) -> None:
    user = User(
        email="probe@example.invalid",
        email_normalized="probe@example.invalid",
        password_hash=secrets.token_hex(32),
        display_name="Probe",
    )
    AccountRepository(db_session).save(user)
    token = SessionTokenService(identity_config, clock).issue(user)
    scope = Scope(build_identity_service(db_session, identity_config, clock))
    factory = ContextFactory(clock)
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    guest = factory.build(Request({"type": "http", "headers": []}), scope)
    public = schema.execute_sync("{ping}", context_value=guest)
    assert public.data == {"ping": True} and public.errors is None
    denied = schema.execute_sync("mutation{identityProbe}", context_value=guest)
    assert denied.errors and denied.errors[0].extensions is not None
    assert denied.errors[0].extensions["code"] == "UNAUTHENTICATED"
    signed_in = factory.build(
        Request({"type": "http", "headers": [(b"authorization", f"Bearer {token.raw}".encode())]}),
        scope,
    )
    accepted = schema.execute_sync("mutation{identityProbe}", context_value=signed_in)
    assert accepted.data == {"identityProbe": user.id} and accepted.errors is None
