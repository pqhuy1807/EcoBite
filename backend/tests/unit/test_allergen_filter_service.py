"""Unit tests for AllergenHardFilterService (Guardrail #7 - hard allergen filter)."""

from app.services.allergen_filter_service import AllergenHardFilterService

DISH_WITH_EGGS = {
    "id": "d1",
    "name": "Bánh mì trứng",
    "allergens": [
        {
            "allergen": "Eggs (Trứng)",
            "risk_level": "HIGH",
            "source": "EXPLICIT",
            "reason": "Có trứng",
        }
    ],
}

DISH_WITH_GLUTEN = {
    "id": "d2",
    "name": "Bánh mì",
    "allergens": [
        {
            "allergen": "Gluten",
            "risk_level": "MEDIUM",
            "source": "INFERRED",
            "reason": "Có bột mì",
        }
    ],
}

DISH_WITH_SOY = {
    "id": "d3",
    "name": "Đậu phụ sốt",
    "allergens": [
        {
            "allergen": "Soybeans (Đậu nành)",
            "risk_level": "HIGH",
            "source": "EXPLICIT",
            "reason": "Có đậu",
        }
    ],
}

DISH_NO_ALLERGENS = {"id": "d4", "name": "Nước coc", "allergens": []}


class TestAllergenHardFilter:
    def test_no_exclusions_keeps_all_dishes(self) -> None:
        dishes = [DISH_WITH_EGGS, DISH_WITH_GLUTEN, DISH_NO_ALLERGENS]
        result = AllergenHardFilterService.filter_dishes_by_allergens(dishes, [])
        assert len(result) == 3
        assert [d["id"] for d in result] == ["d1", "d2", "d4"]

    def test_none_exclusions_keeps_all_dishes(self) -> None:
        dishes = [DISH_WITH_EGGS, DISH_WITH_GLUTEN]
        result = AllergenHardFilterService.filter_dishes_by_allergens(dishes, None)
        assert len(result) == 2

    def test_excludes_eggs_case_insensitive(self) -> None:
        dishes = [DISH_WITH_EGGS, DISH_NO_ALLERGENS]
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            dishes, excluded_allergens=["eggs"]
        )
        assert [d["id"] for d in result] == ["d4"]

    def test_excludes_accents_variant(self) -> None:
        """User writes "đậu phộng", dish has "Đậu Phộng (Peanuts)" — must match."""
        dish = {
            "id": "d5",
            "name": "Bánh kẹo",
            "allergens": [
                {
                    "allergen": "Đậu Phộng (Peanuts)",
                    "risk_level": "HIGH",
                    "source": "EXPLICIT",
                    "reason": "",
                }
            ],
        }
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            [dish], excluded_allergens=["đậu phộng"]
        )
        assert result == []

    def test_excludes_multiple_allergens(self) -> None:
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            [DISH_WITH_EGGS, DISH_WITH_GLUTEN, DISH_WITH_SOY, DISH_NO_ALLERGENS],
            excluded_allergens=["trứng", "Gluten"],
        )
        assert [d["id"] for d in result] == ["d3", "d4"]

    def test_excludes_substring_match(self) -> None:
        """Exclusion "Sữa" should match dish allergen "Milk/Dairy (Sữa)"."""
        dish = {
            "id": "d6",
            "name": "Kem",
            "allergens": [
                {
                    "allergen": "Milk/Dairy (Sữa)",
                    "risk_level": "HIGH",
                    "source": "EXPLICIT",
                    "reason": "",
                }
            ],
        }
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            [dish], excluded_allergens=["Sữa"]
        )
        assert result == []

    def test_plain_string_allergens(self) -> None:
        """Allergens as plain strings (not dicts) must also be filtered."""
        dishes = [
            {"id": "a", "name": "X", "allergens": ["Trứng", "Đậu phộng"]},
            {"id": "b", "name": "Y", "allergens": ["Cá"]},
        ]
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            dishes, excluded_allergens=["đậu phộng"]
        )
        assert [d["id"] for d in result] == ["b"]

    def test_empty_allergens_list_passes(self) -> None:
        result = AllergenHardFilterService.filter_dishes_by_allergens(
            [DISH_NO_ALLERGENS], excluded_allergens=["trứng"]
        )
        assert [d["id"] for d in result] == ["d4"]
