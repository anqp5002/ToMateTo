"""Value object `ResourceRef` — dữ liệu quyền service nạp sẵn cho policy.

Policy không tự truy vấn (SPEC S8 r2 §4, CHI_TIET_LEAD 4.3 dòng 385): service
nạp tài nguyên, truyền `resource_id`/`owner_id` vào đây, rồi policy so với
principal. `owner_id=None` nghĩa là không rõ chủ (ví dụ tài nguyên đã bị xoá) và
**không bao giờ** được coi là "chủ".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceRef:
    """Tham chiếu tối thiểu để kiểm quyền: mã tài nguyên và mã chủ sở hữu."""

    resource_id: int | None = None
    owner_id: int | None = None

    def __post_init__(self) -> None:
        if self.resource_id is not None and self.resource_id <= 0:
            raise ValueError("resource_id phải là số dương hoặc None.")
        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError("owner_id phải là số dương hoặc None.")
