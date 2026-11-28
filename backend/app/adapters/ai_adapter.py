"""Bounded AI provider call and a deterministic injectable test adapter."""

import math
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.exceptions import IntegrationError


@dataclass(frozen=True)
class PublicPost:
    post_id: int
    dish_id: int
    dish_name: str
    caption: str
    restaurant_id: int | None
    restaurant_name: str | None


@dataclass(frozen=True)
class HistoryMessage:
    role: str
    content: str


@dataclass(frozen=True)
class PromptContext:
    question: str
    posts: tuple[PublicPost, ...]
    history: tuple[HistoryMessage, ...] = ()


@dataclass(frozen=True)
class AiCompletion:
    content: str
    post_ids: tuple[int, ...] = ()
    dish_ids: tuple[int, ...] = ()
    restaurant_ids: tuple[int, ...] = ()
    draft: dict[str, object] | None = None


class AiProvider(Protocol):
    def complete(self, context: PromptContext) -> AiCompletion: ...


class AiAdapter:
    """The provider endpoint must accept the structured prompt and return JSON."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 25.0,
        *,
        circuit_breaker_enabled: bool = False,
        failure_threshold: int = 5,
        recovery_seconds: float = 30.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 25:
            raise ValueError("Timeout must be between 0 and 25 seconds.")
        if failure_threshold < 1 or not math.isfinite(recovery_seconds) or recovery_seconds <= 0:
            raise ValueError("Circuit breaker settings must be positive.")
        self._url = url
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._slots = threading.BoundedSemaphore(4)
        # The breaker is an optional proposal pending approval in DOC 7.2-A.
        self._breaker_enabled = circuit_breaker_enabled
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._now = monotonic
        self._lock = threading.Lock()
        self._failures = 0
        self._open_until: float | None = None
        self._probe_running = False
        self._generation = 0

    def _admit(self) -> tuple[int, bool]:
        if not self._breaker_enabled:
            return 0, False
        with self._lock:
            open_until = self._open_until
            probe = open_until is not None
            if open_until is not None:
                if self._now() < open_until or self._probe_running:
                    raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
                self._probe_running = True
            return self._generation, probe

    def _record(self, generation: int, probe: bool, success: bool) -> None:
        if not self._breaker_enabled:
            return
        with self._lock:
            if generation != self._generation:
                return
            if probe:
                self._probe_running = False
            if success:
                self._failures = 0
                if probe:
                    self._open_until = None
                    self._generation += 1
                return
            self._failures += 1
            if probe or self._failures >= self._threshold:
                self._open_until = self._now() + self._recovery
                self._probe_running = False
                self._generation += 1

    def complete(self, context: PromptContext) -> AiCompletion:
        if not self._url or not self._api_key:
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
        generation, probe = self._admit()
        if not self._slots.acquire(blocking=False):
            if probe:
                with self._lock:
                    if generation == self._generation:
                        self._probe_running = False
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
        result: Future[AiCompletion] = Future()

        def execute() -> None:
            try:
                payload = {
                    "question": context.question,
                    "history": [
                        {"role": message.role, "content": message.content}
                        for message in context.history
                    ],
                    "posts": [
                        {
                            "postId": post.post_id,
                            "dishId": post.dish_id,
                            "dishName": post.dish_name,
                            "caption": post.caption,
                            "restaurantId": post.restaurant_id,
                            "restaurantName": post.restaurant_name,
                        }
                        for post in context.posts
                    ],
                }
                with httpx.Client(
                    timeout=self._timeout, follow_redirects=False, trust_env=False
                ) as client:
                    response = client.post(
                        self._url or "",
                        json=payload,
                        headers={"Authorization": f"Bearer {self._api_key}"},
                    )
                    response.raise_for_status()
                    body = response.json()
                if not isinstance(body, dict) or not isinstance(body.get("content"), str):
                    raise ValueError("Invalid provider response.")
                ids: dict[str, tuple[int, ...]] = {}
                for key in ("postIds", "dishIds", "restaurantIds"):
                    value = body.get(key, [])
                    if not isinstance(value, list) or any(
                        type(item) is not int or item <= 0 for item in value
                    ):
                        raise ValueError("Invalid provider references.")
                    ids[key] = tuple(value)
                draft = body.get("draft")
                if draft is not None and not isinstance(draft, dict):
                    raise ValueError("Invalid provider draft.")
                result.set_result(
                    AiCompletion(
                        body["content"], ids["postIds"], ids["dishIds"], ids["restaurantIds"], draft
                    )
                )
            except Exception:
                result.set_exception(
                    IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
                )
            finally:
                self._slots.release()

        try:
            threading.Thread(target=execute, name="assistant-provider", daemon=True).start()
        except Exception:
            self._slots.release()
            self._record(generation, probe, False)
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.") from None
        try:
            # A timed-out thread cannot be cancelled; the semaphore bounds outstanding calls.
            completion = result.result(timeout=self._timeout)
        except TimeoutError as error:
            self._record(generation, probe, False)
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.") from error
        except IntegrationError:
            self._record(generation, probe, False)
            raise
        self._record(generation, probe, True)
        return completion


class AiAdapterFake:
    def __init__(self, response: AiCompletion | None = None) -> None:
        self.response = response
        self.calls: list[PromptContext] = []

    def complete(self, context: PromptContext) -> AiCompletion:
        self.calls.append(context)
        if self.response is None:
            raise IntegrationError(message="Trợ lý đang bận. Vui lòng thử lại sau.")
        return self.response
