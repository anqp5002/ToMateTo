from collections.abc import Iterator
from dataclasses import asdict
from typing import Annotated

import strawberry
from fastapi import Depends, Request
from graphql import GraphQLError
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.types import Info

from app._stubs.errors import DomainError
from app.business.identity.auth_service import SESSION_SECONDS, AuthResult, AuthService
from app.business.identity.session_token_service import unauthenticated
from app.presentation.graphql.context import ContextFactory, SessionVerifier, require_principal


@strawberry.input
class RegisterInput:
    email: str
    password: str
    display_name: str


@strawberry.input
class LoginInput:
    email: str
    password: str


@strawberry.type
class User:
    id: strawberry.ID
    display_name: str
    avatar_url: str | None = None


@strawberry.type
class AuthPayload:
    access_token: str
    expires_in_seconds: int
    user: User


@strawberry.type
class SuccessPayload:
    success: bool


class AuthContext(BaseContext):
    def __init__(self, http_request: Request, service: AuthService) -> None:
        self.http_request = http_request
        self.service = service

    @property
    def session_verifier(self) -> SessionVerifier:
        return self.service.identity


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def get_context(request: Request, session: Annotated[Session, Depends(get_session)]) -> AuthContext:
    state = request.app.state
    return AuthContext(
        request, AuthService(session, state.identity_config, state.clock, state.dummy_hash)
    )


def graphql_error(error: DomainError, detail: str | None = None) -> GraphQLError:
    return GraphQLError(
        error.message,
        extensions={
            "code": error.code,
            "fieldErrors": [asdict(field) for field in error.field_errors],
            **({"detailCode": detail} if detail else {}),
        },
    )


def payload(result: AuthResult) -> AuthPayload:
    return AuthPayload(
        access_token=result.token,
        expires_in_seconds=SESSION_SECONDS,
        user=User(id=strawberry.ID(str(result.user.id)), display_name=result.user.display_name),
    )


@strawberry.type
class Query:
    @strawberry.field
    def viewer(self, info: Info[AuthContext, None]) -> User | None:
        context = info.context
        try:
            verified = ContextFactory(context.http_request.app.state.clock).build(
                context.http_request, context
            )
            principal = require_principal(verified)
            user = context.service.accounts.find_by_id(principal.user_id)
            if user is None or not user.is_active:
                raise unauthenticated()
            return User(id=strawberry.ID(str(user.id)), display_name=user.display_name)
        except DomainError as error:
            raise graphql_error(error, "SESSION_INVALID") from None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def register(self, info: Info[AuthContext, None], input: RegisterInput) -> AuthPayload:
        try:
            return payload(
                info.context.service.register(input.email, input.password, input.display_name)
            )
        except DomainError as error:
            raise graphql_error(error) from None

    @strawberry.mutation
    def login(self, info: Info[AuthContext, None], input: LoginInput) -> AuthPayload:
        try:
            return payload(info.context.service.login(input.email, input.password))
        except DomainError as error:
            raise graphql_error(error, "LOGIN_FAILED") from None

    @strawberry.mutation
    def logout(self, info: Info[AuthContext, None]) -> SuccessPayload:
        try:
            header = info.context.http_request.headers.get("Authorization", "").split()
            if len(header) != 2 or header[0].lower() != "bearer":
                raise unauthenticated()
            info.context.service.logout(header[1])
            return SuccessPayload(success=True)
        except DomainError as error:
            raise graphql_error(error, "SESSION_INVALID") from None


router: GraphQLRouter[AuthContext, None] = GraphQLRouter(
    strawberry.Schema(Query, Mutation), context_getter=get_context
)
