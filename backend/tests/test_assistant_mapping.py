from datetime import UTC, datetime

from app.graphql.assistant import _message
from app.models.chat import ChatMessage


def _row(draft: dict[str, object] | None) -> ChatMessage:
    return ChatMessage(
        id=2,
        session_id=1,
        reply_to_id=1,
        role="assistant",
        status="OK",
        content="Gợi ý món ăn.",
        post_draft=draft,
        processing_version=1,
        created_at=datetime.now(UTC),
    )


def test_message_projects_stored_draft_and_ignores_private_extra_fields() -> None:
    message = _message(
        _row(
            {
                "dishName": "Phở bò",
                "caption": "Ăn trưa",
                "restaurantName": "Quán A",
                "recipe": {"ingredients": ["bánh phở"], "instructions": ["nấu nước dùng"]},
                "providerInternal": "not exposed",
            }
        )
    )
    assert message.draft is not None
    assert message.draft.dish_name == "Phở bò"
    assert message.draft.caption == "Ăn trưa"
    assert message.draft.restaurant_name == "Quán A"
    assert message.draft.recipe is not None
    assert message.draft.recipe.ingredients == ["bánh phở"]
    assert message.draft.recipe.instructions == ["nấu nước dùng"]
    assert not hasattr(message.draft, "providerInternal")


def test_message_without_draft_or_with_malformed_recipe_returns_null() -> None:
    assert _message(_row(None)).draft is None
    assert _message(_row({"dishName": "Phở", "recipe": {"ingredients": [123]}})).draft is None
