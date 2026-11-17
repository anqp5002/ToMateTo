"""Enum hành động ghi cho `WriteAuthorizationPolicy` (SPEC S8 r2 §4, WP43-S8.3)."""

from __future__ import annotations

from enum import StrEnum


class WriteAction(StrEnum):
    """Mười hai hành động ghi cần kiểm quyền trước khi chạm CSDL.

    Dùng `StrEnum` để log/trace đọc được mà vẫn so sánh theo giá trị ổn định.
    """

    CREATE_POST = "CREATE_POST"
    UPDATE_POST = "UPDATE_POST"
    DELETE_POST = "DELETE_POST"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    SET_VISIBILITY = "SET_VISIBILITY"
    LIKE = "LIKE"
    SAVE = "SAVE"
    REPORT = "REPORT"
    FOLLOW = "FOLLOW"
    COLLECTION = "COLLECTION"
    NOTIFICATION = "NOTIFICATION"
    ASSISTANT = "ASSISTANT"
