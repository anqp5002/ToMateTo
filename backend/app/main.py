"""FastAPI application factory with the shared S8 GraphQL request pipeline."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from app.core.config import Config
from app.core.container import AppContainer, RequestScope
from app.core.exceptions import DomainError
from app.graphql.context import ContextFactory, RequestContext
from app.graphql.errors import ErrorMapper
from app.graphql.schema import Query, SafeSchema
from graphql import GraphQLError

logger = logging.getLogger(__name__)


class SafeGraphQLRouter(GraphQLRouter[RequestContext, None]):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if result.errors:
            if all(error.original_error is None and error.path is None for error in result.errors):
                request.state.graphql_pre_execution_error = True
            mapped = []
            for error in result.errors:
                if error.original_error is not None:
                    safe = request.app.state.error_mapper.to_graphql_error(error.original_error)
                    mapped.append(
                        GraphQLError(safe.message, path=error.path, extensions=safe.extensions)
                    )
                else:
                    mapped.append(error)
            result.errors = mapped
        return await super().process_result(request, result)


def create_app(
    config: Config | None = None,
    *,
    container: AppContainer | None = None,
    schema: SafeSchema | None = None,
) -> FastAPI:
    """Build the app explicitly so importing this module never loads secrets."""
    dependencies = container or AppContainer(config or Config.from_env())
    mapper = ErrorMapper()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        if container is None:
            await run_in_threadpool(dependencies.close)

    app = FastAPI(lifespan=lifespan)
    app.state.container = dependencies
    app.state.error_mapper = mapper
    context_factory = ContextFactory(dependencies.clock)

    async def scope_getter() -> AsyncIterator[RequestScope]:
        manager = dependencies.new_scope()
        scope = await run_in_threadpool(manager.__enter__)
        try:
            yield scope
        finally:
            await run_in_threadpool(manager.__exit__, None, None, None)

    async def context_getter(
        request: Request, scope: Annotated[RequestScope, Depends(scope_getter)]
    ) -> RequestContext:
        return await run_in_threadpool(context_factory.build, request, scope)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
        if request.url.path == "/graphql":
            return JSONResponse(
                {"data": None, "errors": [mapper.to_graphql_error(error).formatted]},
                status_code=200,
            )
        return JSONResponse(mapper.to_http_body(error), status_code=mapper.to_http_status(error))

    @app.middleware("http")
    async def request_identifier(request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Accept only UUID correlation IDs to prevent user input or secrets entering logs.
        try:
            request_id = str(UUID(request.headers.get("X-Request-Id", "")))
        except ValueError:
            request_id = str(uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception as error:
            logger.error(
                "request_failed",
                extra={
                    "event": "request_failed",
                    "request_id": request_id,
                    "error_type": type(error).__name__,
                },
            )
            response = JSONResponse(
                {"data": None, "errors": [mapper.to_graphql_error(RuntimeError()).formatted]}
                if request.url.path == "/graphql"
                else mapper.to_http_body(RuntimeError()),
                status_code=200 if request.url.path == "/graphql" else 500,
            )
        response.headers["X-Request-Id"] = request_id
        if getattr(request.state, "graphql_pre_execution_error", False):
            response.status_code = 400
        return response

    router = SafeGraphQLRouter(
        schema or SafeSchema(query=Query),
        context_getter=context_getter,
        graphql_ide=None,
        allow_queries_via_get=False,
    )
    app.include_router(router, prefix="/graphql")
    return app
