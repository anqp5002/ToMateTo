"""Immutable process configuration, loaded explicitly at application startup."""

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Config:
    database_url: str = field(repr=False)
    jwt_secret: str = field(repr=False)
    ai_provider_url: str | None = None
    ai_provider_key: str | None = field(default=None, repr=False)
    cors_origins: tuple[str, ...] = ()
    ai_circuit_breaker_enabled: bool = False
    ai_circuit_failure_threshold: int = 5
    ai_circuit_recovery_seconds: float = 30.0
    trending_tags_enabled: bool = False
    assistant_default_latitude: float = 21.0285
    assistant_default_longitude: float = 105.8542

    def __post_init__(self) -> None:
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL is required.")
        if not self.jwt_secret.strip():
            raise ValueError("JWT_SECRET is required.")
        if bool(self.ai_provider_url) != bool(self.ai_provider_key):
            raise ValueError("AI_PROVIDER_URL and AI_PROVIDER_KEY must be set together.")
        if self.ai_provider_url:
            url = urlsplit(self.ai_provider_url)
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise ValueError("AI_PROVIDER_URL must be an HTTPS URL without credentials.")
        if (
            self.ai_circuit_failure_threshold < 1
            or not math.isfinite(self.ai_circuit_recovery_seconds)
            or self.ai_circuit_recovery_seconds <= 0
        ):
            raise ValueError("AI circuit breaker settings must be positive.")
        if not (-90 <= self.assistant_default_latitude <= 90) or not (
            -180 <= self.assistant_default_longitude <= 180
        ):
            raise ValueError("Assistant default location is invalid.")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Config":
        source = os.environ if environ is None else environ
        enabled = source.get("AI_CIRCUIT_BREAKER_ENABLED", "false").strip().lower()
        if enabled not in {"true", "false"}:
            raise ValueError("AI_CIRCUIT_BREAKER_ENABLED must be true or false.")
        tags_enabled = source.get("TRENDING_TAGS_ENABLED", "false").strip().lower()
        if tags_enabled not in {"true", "false"}:
            raise ValueError("TRENDING_TAGS_ENABLED must be true or false.")
        return cls(
            source.get("DATABASE_URL", ""),
            source.get("JWT_SECRET", ""),
            source.get("AI_PROVIDER_URL") or None,
            source.get("AI_PROVIDER_KEY") or None,
            tuple(
                origin.strip()
                for origin in source.get("CORS_ORIGINS", "").split(",")
                if origin.strip()
            ),
            enabled == "true",
            int(source.get("AI_CIRCUIT_FAILURE_THRESHOLD", "5")),
            float(source.get("AI_CIRCUIT_RECOVERY_SECONDS", "30")),
            tags_enabled == "true",
            float(source.get("ASSISTANT_DEFAULT_LATITUDE", "21.0285")),
            float(source.get("ASSISTANT_DEFAULT_LONGITUDE", "105.8542")),
        )
