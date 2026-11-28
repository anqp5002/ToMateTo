"""Application GraphQL schema with S9 discovery and assistant operations."""

import logging
from collections.abc import Iterable
from typing import Any

import strawberry
from fastapi.concurrency import run_in_threadpool
from strawberry.types.execution import ExecutionContext, ExecutionResult
from strawberry.types.graphql import OperationType

from app.core.exceptions import DomainError
from app.graphql.assistant import AssistantMutation, AssistantQuery
from app.graphql.search import SearchQuery
from app.graphql.trending import TrendingQuery
from graphql import GraphQLError

logger = logging.getLogger(__name__)


@strawberry.type
class Query(SearchQuery, TrendingQuery, AssistantQuery):
    @strawberry.field
    def status(self) -> str:
        """Confirm the GraphQL request pipeline is reachable."""
        return "ready"


@strawberry.type
class Mutation(AssistantMutation):
    pass


class SafeSchema(strawberry.Schema):
    async def execute(
        self,
        query: str | None,
        variable_values: dict[str, Any] | None = None,
        context_value: Any | None = None,
        root_value: Any | None = None,
        operation_name: str | None = None,
        allowed_operation_types: Iterable[OperationType] | None = None,
        operation_extensions: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        # Services use synchronous SQLAlchemy and must run off the HTTP event loop.
        return await run_in_threadpool(
            self.execute_sync,
            query,
            variable_values,
            context_value,
            root_value,
            operation_name,
            allowed_operation_types,
            operation_extensions,
        )

    def process_errors(
        self, errors: list[GraphQLError], execution_context: ExecutionContext | None = None
    ) -> None:
        for error in errors:
            original = error.original_error
            code = original.code if isinstance(original, DomainError) else "INTERNAL_ERROR"
            context = execution_context.context if execution_context is not None else None
            request = getattr(context, "request", None)
            request_id = getattr(getattr(request, "state", None), "request_id", None)
            logger.log(
                logging.ERROR if code == "INTERNAL_ERROR" else logging.WARNING,
                "graphql_error",
                extra={
                    "event": "graphql_error",
                    "code": code,
                    "request_id": request_id,
                    "error_type": type(original).__name__ if original is not None else None,
                },
            )
