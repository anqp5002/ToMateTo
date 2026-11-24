"""NFR-06: 6 characters through 72 UTF-8 bytes, bcrypt cost 12."""

import bcrypt

from app._stubs.errors import FieldError, ValidationError


class PasswordPolicy:
    def validate(self, raw: str) -> None:
        try:
            valid = len(raw) >= 6 and len(raw.encode("utf-8")) <= 72
        except UnicodeError:
            valid = False
        if not valid:
            raise ValidationError(
                "Mật khẩu cần ít nhất 6 ký tự và không vượt quá 72 byte UTF-8.",
                field_errors=(
                    FieldError("password", "PASSWORD_INVALID", "Mật khẩu không hợp lệ."),
                ),
            )

    def hash(self, raw: str) -> str:
        self.validate(raw)
        return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")

    def verify(self, raw: str, stored: str) -> bool:
        try:
            encoded = raw.encode("utf-8")
            if len(raw) < 6 or len(encoded) > 72:
                return False
            return bcrypt.checkpw(encoded, stored.encode("ascii"))
        except (ValueError, UnicodeError):
            return False
