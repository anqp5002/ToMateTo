import pytest
from app.services.assistant_service import _sanitized


@pytest.mark.parametrize(
    "coordinate",
    [
        "21.03, 105.85",
        "-6.2;106.8",
        "21,105",
        "21.03 105.85",
        "lat=21.03 lng=105.85",
        "21°02'30\"N",
    ],
)
def test_common_coordinate_formats_are_redacted(coordinate: str) -> None:
    masked = _sanitized(f"Find food near {coordinate}")
    assert coordinate not in masked
    assert "[đã ẩn vị trí]" in masked


def test_sanitize_before_truncation_masks_coordinate_at_caption_boundary() -> None:
    caption = "x" * 192 + " 21.03, 105.85"
    masked = _sanitized(caption)[:200]
    assert "21.03" not in masked
    assert "105.85" not in masked
