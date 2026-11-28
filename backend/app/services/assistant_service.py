"""Assistant transaction boundaries, owner checks, and bounded public context."""

import re
from dataclasses import dataclass
from typing import Protocol

from app.adapters.ai_adapter import (
    AiCompletion,
    AiProvider,
    HistoryMessage,
    PromptContext,
    PublicPost,
)
from app.core.clock import Clock
from app.core.container import RequestScope
from app.core.exceptions import AuthorizationError, IntegrationError, NotFoundError, ValidationError
from app.core.identity import Principal
from app.core.pagination import PageRequest, RepositoryPage
from app.models.chat import ChatMessage
from app.repositories.chat_repo import (
    AssistantConversationRepository,
    ClaimResult,
    ReplyResult,
    SessionSummary,
)
from app.repositories.search_repo import NearbyCandidate
from app.services.geo import distance_meters

_PRIVATE_DATA = re.compile(
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\bBearer\s+\S+|"
    r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    re.I,
)
_COORDINATES = re.compile(
    r"(?<![\w.])[-+]?\d{1,3}(?:\.\d+)?\s*[,;/]\s*"
    r"[-+]?\d{1,3}(?:\.\d+)?(?![\w.])"
    r"|(?<![\w.])[-+]?\d{1,3}\.\d+\s+[-+]?\d{1,3}\.\d+(?![\w.])"
    r"|\b(?:lat(?:itude)?|lon(?:gitude)?|lng)\s*[:=]\s*"
    r"[-+]?\d{1,3}(?:\.\d+)?\b"
    r"|(?<!\w)\d{1,3}\s*°\s*\d{1,2}(?:[′']\s*\d{1,2}(?:\.\d+)?[″\"]?)?"
    r"(?:\s*[NSEW]\b)?",
    re.I,
)


def _sanitized(value: str) -> str:
    return _COORDINATES.sub("[đã ẩn vị trí]", _PRIVATE_DATA.sub("[đã ẩn]", value))


class WritePolicy(Protocol):
    def authorize_write(self, principal: Principal, action: str) -> None: ...


class NearbyReader(Protocol):
    def find_nearby(
        self, latitude: float, longitude: float, radius_meters: int = 5000
    ) -> list[NearbyCandidate]: ...


class UnavailableWritePolicy:
    def authorize_write(self, principal: Principal, action: str) -> None:
        raise AuthorizationError()


@dataclass(frozen=True)
class AssistantReplyData:
    session_id: int
    message: ChatMessage


class AssistantService:
    def __init__(
        self,
        scope: RequestScope,
        clock: Clock,
        adapter: AiProvider,
        policy: WritePolicy,
        *,
        nearby_reader: NearbyReader,
        default_location: tuple[float, float] | None = None,
    ) -> None:
        self.scope = scope
        self.clock = clock
        self.adapter = adapter
        self.policy = policy
        self.repo = AssistantConversationRepository(scope.session, clock)
        self.nearby_reader = nearby_reader
        self.default_location = default_location

    @staticmethod
    def _user(principal: Principal | None) -> Principal:
        if principal is None:
            raise AuthorizationError("UNAUTHENTICATED")
        return principal

    def ask(
        self,
        message: str,
        session_id: int | None,
        principal: Principal | None,
        location: tuple[float, float] | None = None,
    ) -> AssistantReplyData:
        user = self._user(principal)
        self.policy.authorize_write(user, "askAssistant")
        question = message.strip()
        if not question or len(question) > 2000:
            raise ValidationError()
        # Never forward obvious credentials or personal email to an external model.
        if _PRIVATE_DATA.search(question):
            raise ValidationError(
                message="Vui lòng không gửi email hoặc thông tin đăng nhập cho trợ lý."
            )
        # A location typed into free text must not be persisted or sent to the provider.
        # This is a best-effort filter, not a guarantee for all free-form private data.
        question = _COORDINATES.sub("[đã ẩn vị trí]", question)

        def prepare() -> tuple[int, ClaimResult]:
            conversation = (
                self.repo.create_session(user.user_id)
                if session_id is None
                else self.repo.find_session(session_id, user.user_id)
            )
            if conversation is None:
                raise NotFoundError()
            row = self.repo.save_message(
                ChatMessage(session_id=conversation.id, role="user", content=question, status="OK"),
                user.user_id,
            )
            return conversation.id, self.repo.claim_reply(
                row.id, user.user_id, self.clock.now(), 30
            )

        effective_location = self._location(location)
        sid, claim = self.scope.transaction.run(prepare)
        return self._finish(sid, question, user, claim, effective_location)

    def retry(self, reply_id: int, principal: Principal | None) -> AssistantReplyData:
        user = self._user(principal)
        self.policy.authorize_write(user, "retryAssistant")

        def prepare() -> tuple[int, str, ClaimResult]:
            reply = self.repo.find_message(reply_id, user.user_id)
            if reply is None or reply.role != "assistant" or reply.reply_to_id is None:
                raise NotFoundError()
            question = self.repo.find_message(reply.reply_to_id, user.user_id)
            if (
                question is None
                or question.role != "user"
                or question.session_id != reply.session_id
            ):
                raise NotFoundError()
            return (
                reply.session_id,
                question.content,
                self.repo.claim_reply(question.id, user.user_id, self.clock.now(), 30),
            )

        sid, question, claim = self.scope.transaction.run(prepare)
        return self._finish(sid, question, user, claim, self._location(None))

    def list_sessions(
        self, principal: Principal | None, page: PageRequest
    ) -> RepositoryPage[SessionSummary]:
        user = self._user(principal)
        return self.scope.transaction.run(lambda: self.repo.list_sessions(user.user_id, page))

    def history(
        self, session_id: int | None, principal: Principal | None, page: PageRequest
    ) -> RepositoryPage[ChatMessage]:
        user = self._user(principal)

        def read() -> RepositoryPage[ChatMessage]:
            sid = session_id
            if sid is None:
                sessions = self.repo.list_sessions(user.user_id, PageRequest.of(1)).items
                if not sessions:
                    return RepositoryPage([], False)
                sid = sessions[0].id
            if self.repo.find_session(sid, user.user_id) is None:
                raise NotFoundError()
            return self.repo.list_messages(sid, user.user_id, page)

        return self.scope.transaction.run(read)

    def _location(self, location: tuple[float, float] | None) -> tuple[float, float] | None:
        effective = location if location is not None else self.default_location
        if effective is not None and not (
            -90 <= effective[0] <= 90 and -180 <= effective[1] <= 180
        ):
            raise ValidationError()
        return effective

    def _public_context(
        self, question: str, user_id: int, location: tuple[float, float] | None = None
    ) -> PromptContext:
        if location is None:
            rows = self.repo.list_public_context(user_id, 10)
        else:
            lat, lon = location
            restaurant_ids = {
                candidate.restaurant_id
                for candidate in self.nearby_reader.find_nearby(lat, lon)
                if distance_meters(lat, lon, candidate.latitude, candidate.longitude) <= 5000
            }
            rows = self.repo.list_public_context(user_id, 10, restaurant_ids)
        posts = tuple(
            PublicPost(
                row.post_id,
                row.dish_id,
                _sanitized(row.dish_name),
                _sanitized(row.caption)[:200],
                row.restaurant_id,
                _sanitized(row.restaurant_name) if row.restaurant_name else None,
            )
            for row in rows
        )
        return PromptContext(_sanitized(question), posts)

    def _finish(
        self,
        sid: int,
        question: str,
        user: Principal,
        claim: ClaimResult,
        location: tuple[float, float] | None = None,
    ) -> AssistantReplyData:
        if claim.state != "CLAIMED":
            return AssistantReplyData(sid, claim.current_reply)
        context = self.scope.transaction.run(
            lambda: self._prompt_context(sid, question, user.user_id, claim.reply_id, location)
        )
        unavailable = False
        try:
            candidate = self.adapter.complete(context)
            if not candidate.content.strip():
                raise IntegrationError()
            result = self.scope.transaction.run(
                lambda: self._validated(candidate, context, user.user_id, location)
            )
        except IntegrationError:
            unavailable = True
            result = self.scope.transaction.run(
                lambda: self._fallback(context, user.user_id, location)
            )
        committed = self.scope.transaction.run(
            lambda: self.repo.complete_reply(
                claim.reply_id, user.user_id, claim.processing_version, result, self.clock.now()
            )
        )
        current = self.scope.transaction.run(
            lambda: self.repo.find_message(claim.reply_id, user.user_id)
        )
        if current is None:
            raise NotFoundError()
        if unavailable and committed:
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
        return AssistantReplyData(sid, current)

    def _prompt_context(
        self,
        session_id: int,
        question: str,
        user_id: int,
        reply_id: int,
        location: tuple[float, float] | None = None,
    ) -> PromptContext:
        context = self._public_context(question, user_id, location)
        rows = self.repo.list_history_before(reply_id, session_id, user_id, 10)
        history = tuple(
            HistoryMessage(row.role, _sanitized(row.content)[:2000]) for row in reversed(rows)
        )
        return PromptContext(context.question, context.posts, history)

    def _validated(
        self,
        candidate: AiCompletion,
        context: PromptContext,
        user_id: int,
        location: tuple[float, float] | None = None,
    ) -> ReplyResult:
        current = self._public_context(context.question, user_id, location)
        visible = {p.post_id: p for p in current.posts}
        allowed = [visible[p.post_id] for p in context.posts if p.post_id in visible]
        # Ignore references not found in the freshly checked, visible context.
        # Provider prose is not used, so dropped references cannot leak via text.
        post_ids = set(candidate.post_ids) & {p.post_id for p in allowed}
        dish_ids = set(candidate.dish_ids) & {p.dish_id for p in allowed}
        restaurant_ids = set(candidate.restaurant_ids) & {
            p.restaurant_id for p in allowed if p.restaurant_id is not None
        }
        selected = next(
            (
                post
                for post in allowed
                if post.post_id in post_ids
                or post.dish_id in dish_ids
                or post.restaurant_id in restaurant_ids
            ),
            None,
        )
        if selected is None:
            raise IntegrationError()
        # S9: câu mẫu từ dữ liệu đã kiểm; S10 cần kiểm nội dung AI trước khi đo NFR-15.
        answer = "Bạn có thể tham khảo món " + selected.dish_name
        if selected.restaurant_name:
            answer += " tại " + selected.restaurant_name
        return ReplyResult("OK", answer + ".", None)

    def _fallback(
        self, context: PromptContext, user_id: int, location: tuple[float, float] | None = None
    ) -> ReplyResult:
        visible = {
            p.post_id: p for p in self._public_context(context.question, user_id, location).posts
        }
        posts = [visible[p.post_id] for p in context.posts if p.post_id in visible]
        if not posts:
            return ReplyResult("FAILED", "")
        return ReplyResult("FALLBACK", "Bạn có thể tham khảo món " + posts[0].dish_name + ".")
