"""`follow_repository` — đọc/ghi T13 `follows` (chữ ký 6.1-A BE dòng 737-741).

Không commit. `set_state` trả `changed` như `LikeRepository.set_state` để
service chỉ phát thông báo FOLLOW khi quan hệ thực sự đổi.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.social.follow import Follow


@dataclass(frozen=True, slots=True)
class FollowCounts:
    """Số người theo dõi và số người đang theo dõi một tài khoản."""

    followers: int
    following: int


class FollowRepository:
    """Truy vấn quan hệ theo dõi; nhận `Session` qua constructor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def set_state(self, follower_id: int, followee_id: int, followed: bool) -> bool:
        """Theo dõi/bỏ theo dõi; trả `True` khi quan hệ thực sự đổi.

        Theo dõi lặp lại là no-op (`ON CONFLICT DO NOTHING`). Chặn tự theo dõi
        là việc của service; CSDL cũng có CHECK `ck_follows_not_self` chặn lần
        cuối nên `IntegrityError` sẽ nổi lên nếu service bỏ sót.
        """
        if followed:
            result = self._session.execute(
                insert(Follow)
                .values(follower_id=follower_id, followee_id=followee_id)
                .on_conflict_do_nothing(index_elements=[Follow.follower_id, Follow.followee_id])
                .returning(Follow.follower_id)
            )
            return result.first() is not None

        removed = self._session.execute(
            delete(Follow).where(
                Follow.follower_id == follower_id, Follow.followee_id == followee_id
            )
        )
        return bool(removed.rowcount)

    def is_following(self, follower_id: int, followee_id: int) -> bool:
        """`follower_id` có đang theo dõi `followee_id` không."""
        return bool(
            self._session.scalar(
                select(
                    exists().where(
                        Follow.follower_id == follower_id,
                        Follow.followee_id == followee_id,
                    )
                )
            )
        )

    def counts(self, user_id: int) -> FollowCounts:
        """`(followers, following)` của một tài khoản — hai COUNT trong một câu."""
        row = self._session.execute(
            select(
                func.count().filter(Follow.followee_id == user_id).label("followers"),
                func.count().filter(Follow.follower_id == user_id).label("following"),
            ).select_from(Follow)
        ).one()
        return FollowCounts(followers=int(row.followers or 0), following=int(row.following or 0))
