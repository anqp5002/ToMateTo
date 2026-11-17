"""STUB điểm nối 4 — vai BE (`Clock`) sẽ thay.

Nguồn thời gian duy nhất, tz-aware UTC (DOC 6.1-A BE §5.7). Test dịch vụ dùng
`FixedClock` thay vì ngủ thật.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime


class Clock:
    """Đồng hồ hệ thống, luôn trả thời điểm UTC có múi giờ."""

    def now(self) -> datetime:
        return datetime.now(tz=UTC)

    def today(self) -> date:
        return self.now().date()


@dataclass(frozen=True, slots=True)
class FixedClock(Clock):
    """Đồng hồ cố định cho test; từ chối thời điểm không có múi giờ."""

    instant: datetime

    def __post_init__(self) -> None:
        if self.instant.tzinfo is None:
            raise ValueError("FixedClock cần thời điểm có múi giờ.")

    def now(self) -> datetime:
        return self.instant
