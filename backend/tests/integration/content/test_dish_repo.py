import unicodedata

import pytest
from sqlalchemy.orm import Session
from tomateto.dataaccess.content.dish_repo import DishRepository
from tomateto.dataaccess.content.restaurant_repo import RestaurantRepository


@pytest.mark.parametrize("name", ["PHỞ BÒ", "  Phở   Bò  ", unicodedata.normalize("NFD", "Phở bò")])
def test_dish_normalization_reuses_existing_row(session: Session, name: str) -> None:
    assert DishRepository(session).upsert(name).id == 1


def test_dish_d_stroke_and_rollback(session: Session) -> None:
    dish = DishRepository(session).upsert("  BÁNH   ĐẬU XANH ")
    assert dish.name_normalized == "banh dau xanh"
    assert DishRepository(session).upsert("bánh đậu xanh").id == dish.id


def test_restaurants_do_not_gain_an_undocumented_unique_name(session: Session) -> None:
    repo = RestaurantRepository(session)
    first = repo.create("Quán trùng", "Địa chỉ A", latitude=21.0285, longitude=105.8542)
    other = repo.create("QUÁN TRÙNG", "Địa chỉ B", latitude=21.03, longitude=105.86)
    assert first.id != other.id and len(repo.find_candidates_by_name("quán trùng")) == 2
    with pytest.raises(ValueError, match="Multiple restaurants"):
        repo.find_by_name_normalized("quán trùng")
