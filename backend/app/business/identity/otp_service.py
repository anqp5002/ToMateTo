"""Salted HMAC hashes keep low-entropy OTPs safe from a database-only leak."""

import hashlib
import hmac
import re
import secrets

from app.business.identity.config import IdentityConfig


class OtpService:
    def __init__(self, config: IdentityConfig) -> None:
        self._pepper = config.otp_pepper.encode("utf-8")

    def generate(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def hash(self, code: str) -> str:
        if re.fullmatch(r"[0-9]{6}", code) is None:
            raise ValueError("OTP must contain exactly six ASCII digits.")
        salt = secrets.token_hex(16)
        digest = hmac.new(self._pepper, f"{salt}:{code}".encode(), hashlib.sha256).hexdigest()
        return f"v1${salt}${digest}"

    def verify(self, code: str, stored: str) -> bool:
        if re.fullmatch(r"[0-9]{6}", code) is None:
            return False
        parts = stored.split("$")
        if (
            len(parts) != 3
            or parts[0] != "v1"
            or re.fullmatch(r"[0-9a-f]{32}", parts[1]) is None
            or re.fullmatch(r"[0-9a-f]{64}", parts[2]) is None
        ):
            return False
        actual = hmac.new(self._pepper, f"{parts[1]}:{code}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(actual, parts[2])
