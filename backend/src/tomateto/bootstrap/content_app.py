"""Composition entry point. Identity and B10 implementations remain injectable group ports."""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

from tomateto.business.content.contracts import ContentWritePolicy, TimeSource, WritePolicy, invalid
from tomateto.business.content.media_service import MediaService
from tomateto.dataaccess.schema import media_assets
from tomateto.integration.media_storage import MAX_UPLOAD_BYTES, LocalMediaStorage
from tomateto.presentation.content_graphql import ContentContext, schema
from tomateto.presentation.errors import ErrorMapper
from tomateto.shared.clock import Clock
from tomateto.shared.exceptions import AuthorizationError, DomainError
from tomateto.shared.identity import Principal, SessionVerifier, UnavailableSessionVerifier


class GraphQLRequest(BaseModel):
    query: str
    variables: dict[str, Any] | None = None
    operationName: str | None = None  # noqa: N815


def create_app(
    session_factory: Callable[[], Session],
    *,
    storage_root: Path,
    verifier_factory: Callable[[Session], SessionVerifier] | None = None,
    policy: WritePolicy | None = None,
    clock: TimeSource | None = None,
    cors_origins: list[str] | None = None,
    upload_guard: Callable[[int], None] | None = None,
) -> FastAPI:
    app = FastAPI(title="ToMateTo Content")
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["X-Request-Id"],
        )
    storage = LocalMediaStorage(storage_root)
    write_policy, time_source = policy or ContentWritePolicy(), clock or Clock()
    verifier_for = verifier_factory or (lambda _: UnavailableSessionVerifier())
    mapper = ErrorMapper()

    def principal(request: Request, session: Session) -> Principal | None:
        header = request.headers.get("Authorization")
        if header is None:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthorizationError("UNAUTHENTICATED")
        return verifier_for(session).verify_session(parts[1])

    @app.middleware("http")
    async def request_id(request: Request, call_next: Any) -> Any:
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(mapper.to_http_body(error), status_code=mapper.to_http_status(error))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            mapper.to_http_body(error),
            status_code=500,
            headers={"X-Request-Id": request.state.request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            mapper.to_http_body(DomainError("VALIDATION_FAILED")),
            status_code=400,
            headers={"X-Request-Id": request.state.request_id},
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        safe = DomainError("VALIDATION_FAILED" if error.status_code == 400 else "NOT_FOUND")
        return JSONResponse(mapper.to_http_body(safe), status_code=error.status_code)

    @app.post("/graphql")
    def graphql(body: GraphQLRequest, request: Request) -> dict[str, Any]:
        with session_factory() as session:
            error = None
            try:
                viewer = principal(request, session)
            except DomainError as rejected:
                viewer, error = None, rejected
            # End verifier read transaction before service-owned writes.
            session.rollback()
            ctx = ContentContext(session, viewer, write_policy, time_source, error)
            result = schema.execute_sync(
                body.query,
                variable_values=body.variables,
                operation_name=body.operationName,
                context_value=ctx,
            )
            response: dict[str, Any] = {"data": result.data}
            if result.errors:
                response["errors"] = [
                    {
                        "message": e.message,
                        "extensions": e.extensions or {"code": "VALIDATION_FAILED"},
                    }
                    for e in result.errors
                ]
            return response

    @app.post("/media/uploads")
    async def upload(request: Request) -> JSONResponse:
        def authenticate() -> Principal | None:
            with session_factory() as session:
                viewer = principal(request, session)
                owner = write_policy.authorize_write(viewer, "uploadMedia")
                if upload_guard:
                    upload_guard(owner)
                return viewer

        viewer = await run_in_threadpool(authenticate)
        if not request.headers.get("content-type", "").lower().startswith("multipart/form-data;"):
            raise DomainError("UNSUPPORTED_MEDIA_TYPE")
        async with request.form(max_files=1, max_fields=1) as form:
            file, purpose = form.get("file"), form.get("purpose")
            if not isinstance(file, UploadFile) or not isinstance(purpose, str):
                raise invalid("file")
            content = await file.read(MAX_UPLOAD_BYTES + 1)

        def write() -> JSONResponse:
            with session_factory() as session:
                asset = MediaService(session, storage, write_policy, time_source).upload(
                    viewer, purpose, content
                )
                return JSONResponse(
                    {
                        "uploadId": str(asset.id),
                        "url": asset.url,
                        "purpose": asset.purpose,
                        "width": asset.width,
                        "height": asset.height,
                        "expiresAt": asset.expires_at.isoformat(),
                    },
                    status_code=201,
                )

        return await run_in_threadpool(write)

    @app.get("/media/{asset_id}")
    def media(asset_id: UUID, request: Request) -> FileResponse:
        with session_factory() as session:
            viewer = principal(request, session)
            viewer_id = viewer.user_id if viewer else None
            asset = session.execute(select(media_assets).where(media_assets.c.id == asset_id))
            row = asset.mappings().first()
            if row is None or row["state"] not in {"PENDING", "ATTACHED"}:
                raise DomainError("NOT_AVAILABLE")
            permitted = row["owner_id"] == viewer_id
            if not permitted and row["state"] == "ATTACHED":
                permitted = bool(
                    session.execute(
                        text("""
                  SELECT EXISTS(SELECT 1 FROM post_images pi JOIN posts p ON p.id=pi.post_id
                  WHERE pi.media_id=:asset AND NOT p.is_hidden AND
                  (CAST(:viewer AS bigint) IS NULL OR NOT EXISTS(SELECT 1 FROM user_blocks b
                    WHERE (b.blocker_id=:viewer AND b.blocked_id=p.user_id)
                       OR (b.blocked_id=:viewer AND b.blocker_id=p.user_id))))
                  OR EXISTS(SELECT 1 FROM users u WHERE
                    ((u.avatar_media_id=:asset AND 'avatarUrl'=ANY(u.public_profile_fields)) OR
                     (u.cover_media_id=:asset AND 'coverUrl'=ANY(u.public_profile_fields))) AND
                    (CAST(:viewer AS bigint) IS NULL OR NOT EXISTS(SELECT 1 FROM user_blocks b
                     WHERE (b.blocker_id=:viewer AND b.blocked_id=u.id)
                        OR (b.blocked_id=:viewer AND b.blocker_id=u.id))))
                """),
                        {"asset": asset_id, "viewer": viewer_id},
                    ).scalar_one()
                )
            if not permitted:
                raise DomainError("NOT_AVAILABLE")
            try:
                path = storage.path(row["storage_key"])
            except ValueError:
                raise DomainError("NOT_AVAILABLE") from None
            if not path.is_file():
                raise DomainError("NOT_AVAILABLE")
            return FileResponse(
                path,
                media_type=row["mime_type"],
                headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
            )

    return app
