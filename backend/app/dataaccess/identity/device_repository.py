"""T04 storage; push-token reassignment is an explicit service decision."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.identity.user_device import UserDevice


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, device: UserDevice) -> None:
        self._session.add(device)
        self._session.flush()

    def remove(self, user_id: int, token: str) -> None:
        self._session.execute(
            delete(UserDevice).where(UserDevice.user_id == user_id, UserDevice.push_token == token)
        )

    def list_by_user(self, user_id: int) -> list[UserDevice]:
        return list(
            self._session.scalars(
                select(UserDevice).where(UserDevice.user_id == user_id).order_by(UserDevice.id)
            )
        )
