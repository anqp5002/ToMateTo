import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from app.adapters.ai_adapter import AiAdapter, PromptContext
from app.core.exceptions import IntegrationError


def test_unconfigured_ai_fails_closed() -> None:
    with pytest.raises(IntegrationError):
        AiAdapter().complete(PromptContext("Xin gợi ý", ()))


def test_wall_clock_timeout_bounds_slow_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    class SlowClient:
        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "SlowClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def post(self, *args: object, **kwargs: object) -> None:
            time.sleep(0.3)
            raise RuntimeError("internal provider secret")

    monkeypatch.setattr("app.adapters.ai_adapter.httpx.Client", SlowClient)
    started = time.monotonic()
    with pytest.raises(IntegrationError) as error:
        AiAdapter("https://example.invalid", "fixture", 0.05).complete(PromptContext("gợi ý", ()))
    assert time.monotonic() - started < 0.2
    assert "secret" not in str(error.value)


class ProviderStub:
    calls = 0
    failures = 0
    started = Event()
    release = Event()
    block = False

    def __init__(self, **kwargs: object) -> None:
        pass

    def __enter__(self) -> "ProviderStub":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def post(self, *args: object, **kwargs: object) -> "ProviderStub":
        type(self).calls += 1
        if type(self).block:
            type(self).started.set()
            assert type(self).release.wait(timeout=2)
        if type(self).failures:
            type(self).failures -= 1
            raise RuntimeError("provider failed")
        return self

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, object]:
        return {"content": "ok", "postIds": [1]}


def test_circuit_breaker_open_half_open_and_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderStub.calls = 0
    ProviderStub.failures = 6
    ProviderStub.block = False
    now = [0.0]
    monkeypatch.setattr("app.adapters.ai_adapter.httpx.Client", ProviderStub)
    adapter = AiAdapter(
        "https://example.invalid", "fixture", circuit_breaker_enabled=True, monotonic=lambda: now[0]
    )
    prompt = PromptContext("gợi ý", ())
    for _ in range(5):
        with pytest.raises(IntegrationError):
            adapter.complete(prompt)
    with pytest.raises(IntegrationError):
        adapter.complete(prompt)
    assert ProviderStub.calls == 5
    now[0] = 30
    with pytest.raises(IntegrationError):
        adapter.complete(prompt)
    assert ProviderStub.calls == 6
    now[0] = 59
    with pytest.raises(IntegrationError):
        adapter.complete(prompt)
    assert ProviderStub.calls == 6
    now[0] = 60
    assert adapter.complete(prompt).post_ids == (1,)
    assert adapter.complete(prompt).post_ids == (1,)
    assert ProviderStub.calls == 8


def test_circuit_breaker_allows_one_half_open_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderStub.calls = 0
    ProviderStub.failures = 1
    ProviderStub.block = False
    ProviderStub.started.clear()
    ProviderStub.release.clear()
    now = [0.0]
    monkeypatch.setattr("app.adapters.ai_adapter.httpx.Client", ProviderStub)
    adapter = AiAdapter(
        "https://example.invalid",
        "fixture",
        circuit_breaker_enabled=True,
        failure_threshold=1,
        monotonic=lambda: now[0],
    )
    prompt = PromptContext("gợi ý", ())
    with pytest.raises(IntegrationError):
        adapter.complete(prompt)
    now[0] = 30
    ProviderStub.block = True
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(adapter.complete, prompt)
        try:
            assert ProviderStub.started.wait(timeout=1)
            with pytest.raises(IntegrationError):
                adapter.complete(prompt)
            assert ProviderStub.calls == 2
        finally:
            ProviderStub.release.set()
        assert future.result(timeout=2).post_ids == (1,)
    ProviderStub.block = False
    assert adapter.complete(prompt).post_ids == (1,)


def test_breaker_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    ProviderStub.calls = 0
    ProviderStub.failures = 6
    ProviderStub.block = False
    monkeypatch.setattr("app.adapters.ai_adapter.httpx.Client", ProviderStub)
    adapter = AiAdapter("https://example.invalid", "fixture")
    for _ in range(6):
        with pytest.raises(IntegrationError):
            adapter.complete(PromptContext("gợi ý", ()))
    assert ProviderStub.calls == 6
    assert adapter.complete(PromptContext("gợi ý", ())).post_ids == (1,)
