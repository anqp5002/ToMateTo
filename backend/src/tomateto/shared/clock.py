"""A replaceable source of timezone-aware UTC time."""

from datetime import UTC, date, datetime


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def today(self) -> date:
        return self.now().date()
