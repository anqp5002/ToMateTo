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
