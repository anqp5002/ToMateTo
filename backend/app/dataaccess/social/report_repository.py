"""`report_repository` — T16 `reports` (chữ ký 6.1-A BE dòng 486-490).

Không có `count_for_post`: báo cáo **không** dùng để tự ẩn bài (5.3-B T16).
Không commit; `insert` chỉ thêm và flush để lấy `id`/`created_at`.
"""

from __future__ import annotations

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.domain.social.report import Report


class ReportRepository:
    """Đọc/ghi báo cáo; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def insert(self, report: Report) -> Report:
        """Thêm báo cáo mới; trả thực thể đã có `id` (chưa commit)."""
        self._session.add(report)
        self._session.flush()
        self._session.refresh(report)
        return report

    def exists_for_user(self, reporter_id: int, original_post_id: int) -> bool:
        """Người này đã báo cáo bài gốc này chưa (dùng chặn báo trùng)."""
        return bool(
            self._session.scalar(
                select(
                    exists().where(
                        Report.reporter_id == reporter_id,
                        Report.original_post_id == original_post_id,
                    )
                )
            )
        )
