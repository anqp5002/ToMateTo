"""`block_repository` — T25 `user_blocks` (chữ ký 6.1-A BE dòng 486-496).

`list_blocked_user_ids` lọc **hai chiều** (O6, SPEC §7): trả cả người `viewer`
đã chặn lẫn người đã chặn `viewer`, trong **một** truy vấn, không trùng.
Không commit (bảng chỉ đọc trong S8).
"""

from __future__ import annotations

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.domain.social.user_block import UserBlock


class BlockRepository:
    """Truy vấn quan hệ chặn; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_blocked_user_ids(self, viewer_id: int) -> list[int]:
        """Mã những người phải ẩn với `viewer`, theo cả hai chiều, đã sắp xếp.

        Một câu `SELECT DISTINCT CASE …` trên các dòng có `viewer` ở một trong hai
        cột: dòng `viewer → X` trả `X`, dòng `X → viewer` cũng trả `X`. Nhờ
        `DISTINCT`, chặn chéo hai chiều vẫn chỉ ra một mã.
        """
        other_side = case(
            (UserBlock.blocker_id == viewer_id, UserBlock.blocked_id),
            else_=UserBlock.blocker_id,
        )
        rows = self._session.scalars(
            select(other_side)
            .where(or_(UserBlock.blocker_id == viewer_id, UserBlock.blocked_id == viewer_id))
            .distinct()
            .order_by(other_side)
        )
        return [int(user_id) for user_id in rows]
