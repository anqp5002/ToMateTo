from dataclasses import FrozenInstanceError

import pytest
from app.core.config import Config


def test_config_rejects_missing_required_environment() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Config.from_env({})
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Config.from_env({"DATABASE_URL": "postgresql+psycopg://localhost/test"})


def test_config_is_immutable_and_hides_credentials() -> None:
    config = Config.from_env(
        {"DATABASE_URL": "postgresql+psycopg://db/test", "JWT_SECRET": "fixture-key"}
    )
    assert config.jwt_secret == "fixture-key"  # noqa: S105 - public test fixture
    assert "fixture-key" not in repr(config)
    assert "postgresql" not in repr(config)
    with pytest.raises(FrozenInstanceError):
        config.jwt_secret = "changed"  # type: ignore[misc]  # noqa: S105


def test_ai_configuration_requires_https_and_both_values() -> None:
    with pytest.raises(ValueError, match="must be set together"):
        Config("postgresql+psycopg://db/test", "fixture", "https://ai.example", None)
    with pytest.raises(ValueError, match="HTTPS"):
        Config("postgresql+psycopg://db/test", "fixture", "http://ai.example", "fixture")
    config = Config.from_env(
        {
            "DATABASE_URL": "postgresql+psycopg://db/test",
            "JWT_SECRET": "fixture",
            "AI_PROVIDER_URL": "https://ai.example/complete",
            "AI_PROVIDER_KEY": "secret-for-test-only",
            "CORS_ORIGINS": "http://localhost:3000, http://localhost:5000",
        }
    )
    assert config.cors_origins == ("http://localhost:3000", "http://localhost:5000")
    assert "secret-for-test-only" not in repr(config)


def test_ai_breaker_is_optional_and_configurable() -> None:
    env = {"DATABASE_URL": "postgresql+psycopg://db/test", "JWT_SECRET": "fixture"}
    default = Config.from_env(env)
    assert not default.ai_circuit_breaker_enabled
    assert default.ai_circuit_failure_threshold == 5
    assert default.ai_circuit_recovery_seconds == 30
    configured = Config.from_env(
        env
        | {
            "AI_CIRCUIT_BREAKER_ENABLED": "true",
            "AI_CIRCUIT_FAILURE_THRESHOLD": "3",
            "AI_CIRCUIT_RECOVERY_SECONDS": "12.5",
        }
    )
    assert configured.ai_circuit_breaker_enabled
    assert configured.ai_circuit_failure_threshold == 3
    assert configured.ai_circuit_recovery_seconds == 12.5
    with pytest.raises(ValueError, match="ENABLED"):
        Config.from_env(env | {"AI_CIRCUIT_BREAKER_ENABLED": "yes"})
    with pytest.raises(ValueError, match="positive"):
        Config.from_env(env | {"AI_CIRCUIT_RECOVERY_SECONDS": "nan"})
    with pytest.raises(ValueError, match="positive"):
        Config.from_env(env | {"AI_CIRCUIT_FAILURE_THRESHOLD": "0"})


def test_app_passes_breaker_settings_to_ai_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.main import create_app

    captured: dict[str, object] = {}

    def fake_adapter(*args: object, **kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("app.main.AiAdapter", fake_adapter)
    config = Config.from_env(
        {
            "DATABASE_URL": "postgresql+psycopg://db/test",
            "JWT_SECRET": "fixture",
            "AI_CIRCUIT_BREAKER_ENABLED": "true",
            "AI_CIRCUIT_FAILURE_THRESHOLD": "3",
            "AI_CIRCUIT_RECOVERY_SECONDS": "12.5",
        }
    )
    create_app(config)
    assert captured == {
        "circuit_breaker_enabled": True,
        "failure_threshold": 3,
        "recovery_seconds": 12.5,
    }


def test_trending_tags_require_explicit_opt_in() -> None:
    env = {"DATABASE_URL": "postgresql+psycopg://db/test", "JWT_SECRET": "fixture"}
    assert not Config.from_env(env).trending_tags_enabled
    assert Config.from_env(env | {"TRENDING_TAGS_ENABLED": "true"}).trending_tags_enabled
    with pytest.raises(ValueError, match="TRENDING_TAGS_ENABLED"):
        Config.from_env(env | {"TRENDING_TAGS_ENABLED": "yes"})
