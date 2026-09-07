import random

import pytest

from dndnd.domain.characters import (
    POINT_BUY_BUDGET,
    AbilityScoreMethod,
    CharacterDraft,
    DerivedValues,
    ability_modifier,
    ancestry_speed,
    apply_ancestry_bonuses,
    apply_background_bonuses,
    assign_scores_by_class,
    build_random_draft,
    derive_values,
    generate_ability_scores,
    generate_name,
    point_buy_total,
    random_concept,
    validate_draft,
)
from dndnd.models import CharacterAncestry, CharacterClass, CharacterKind, Player
from dndnd.ui.pages.party import build_roll_board


def test_random_character_draft_is_level_one_and_engine_ready() -> None:
    player = Player(id=7, name="Player One", campaign_id=1)
    rng = random.Random(42)

    draft = build_random_draft(set(), [player], rng)

    assert draft.level == 1
    assert draft.kind in [item.value for item in CharacterKind]
    assert draft.ancestry in [item.value for item in CharacterAncestry]
    assert draft.class_name in [item.value for item in CharacterClass]
    assert set(draft.ability_scores) == {
        "Strength",
        "Dexterity",
        "Constitution",
        "Intelligence",
        "Wisdom",
        "Charisma",
    }
    assert draft.player_id == 7
    assert draft.derived.max_hp > 0
    assert draft.derived.armor_class > 0


def test_dice_roll_scores_are_valid_for_4d6_drop_lowest() -> None:
    rng = random.Random(7)
    scores = generate_ability_scores(AbilityScoreMethod.DICE_4D6_DROP_LOWEST, rng)

    assert set(scores) == {
        "Strength",
        "Dexterity",
        "Constitution",
        "Intelligence",
        "Wisdom",
        "Charisma",
    }
    assert all(3 <= score <= 18 for score in scores.values())


def test_roll_board_preserves_landed_scores_and_hides_active_score() -> None:
    board = "\n".join(
        build_roll_board("Dice roll (4d6, drop lowest)", {"Strength": 15}, "Dexterity", 2)
    )

    assert "Strength** · **15" in board
    assert "Dexterity** · rolling" in board
    assert "Dexterity** · **" not in board
    assert "Constitution** · waiting" in board


def test_point_buy_uses_the_27_point_budget() -> None:
    standard_point_buy = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }

    assert POINT_BUY_BUDGET == 27
    assert point_buy_total(standard_point_buy) == POINT_BUY_BUDGET


def test_domain_standard_array_returns_exact_values() -> None:
    rng = random.Random(7)
    scores = generate_ability_scores(AbilityScoreMethod.STANDARD_ARRAY, rng)

    assert sorted(scores.values()) == [8, 10, 12, 13, 14, 15]
    assert set(scores) == {
        "Strength",
        "Dexterity",
        "Constitution",
        "Intelligence",
        "Wisdom",
        "Charisma",
    }


def test_domain_4d6_drop_lowest_scores_are_in_valid_range() -> None:
    rng = random.Random(42)
    scores = generate_ability_scores(AbilityScoreMethod.DICE_4D6_DROP_LOWEST, rng)

    assert set(scores) == {
        "Strength",
        "Dexterity",
        "Constitution",
        "Intelligence",
        "Wisdom",
        "Charisma",
    }
    assert all(3 <= score <= 18 for score in scores.values())


def test_domain_point_buy_returns_valid_27_point_scores() -> None:
    rng = random.Random(99)
    scores = generate_ability_scores(AbilityScoreMethod.POINT_BUY, rng)

    assert all(8 <= score <= 15 for score in scores.values())
    assert point_buy_total(scores) == POINT_BUY_BUDGET


def test_domain_manual_entry_raises_clear_error() -> None:
    rng = random.Random(0)

    with pytest.raises(ValueError, match="Manual ability scores"):
        generate_ability_scores(AbilityScoreMethod.MANUAL, rng)


def test_domain_class_assignment_places_highest_scores_by_priority() -> None:
    scores = [15, 14, 13, 12, 10, 8]
    assigned = assign_scores_by_class(scores, "Wizard")

    assert assigned["Intelligence"] == 15
    assert assigned["Dexterity"] == 14
    assert assigned["Constitution"] == 13
    assert assigned["Wisdom"] == 12
    assert assigned["Charisma"] == 10
    assert assigned["Strength"] == 8


def test_domain_class_assignment_respects_constitution_priority() -> None:
    assigned = assign_scores_by_class([15, 14, 13, 12, 10, 8], "Barbarian")

    assert assigned["Strength"] == 15
    assert assigned["Constitution"] == 14
    assert assigned["Dexterity"] == 13


def test_domain_ancestry_bonuses_apply_plus_two_plus_one() -> None:
    scores = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    updated = apply_ancestry_bonuses(scores, "Elf")

    assert updated["Dexterity"] == 16
    assert updated["Intelligence"] == 13


def test_domain_human_adds_plus_one_to_three_highest_scores() -> None:
    scores = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    updated = apply_ancestry_bonuses(scores, "Human")

    assert updated["Strength"] == 16
    assert updated["Dexterity"] == 15
    assert updated["Constitution"] == 14
    assert updated["Intelligence"] == 12
    assert updated["Wisdom"] == 10
    assert updated["Charisma"] == 8


def test_domain_goliath_has_35_speed() -> None:
    assert ancestry_speed("Goliath") == 35
    assert ancestry_speed("Human") == 30


def test_domain_background_bonuses_apply_fixed_pair_and_proficiencies() -> None:
    scores = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    updated, proficiencies = apply_background_bonuses(scores, "Soldier")

    assert updated["Strength"] == 17
    assert updated["Constitution"] == 14
    assert proficiencies == ["Athletics", "Intimidation"]


def test_domain_bonuses_respect_twenty_cap() -> None:
    scores = {
        "Strength": 20,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    updated = apply_ancestry_bonuses(scores, "Orc")

    assert updated["Strength"] == 20


def test_domain_bonus_order_is_independent_for_final_cap() -> None:
    scores = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    after_background_first, _ = apply_background_bonuses(scores, "Soldier")
    after_both_background_first = apply_ancestry_bonuses(after_background_first, "Orc")

    after_ancestry_first = apply_ancestry_bonuses(scores, "Orc")
    after_both_ancestry_first, _ = apply_background_bonuses(after_ancestry_first, "Soldier")

    assert after_both_background_first == after_both_ancestry_first


def test_domain_derived_values_for_fighter() -> None:
    scores = {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 12,
        "Wisdom": 10,
        "Charisma": 8,
    }
    derived = derive_values(scores, "Fighter", "Human", level=1)

    assert derived.armor_class == 12
    assert derived.max_hp == 11  # d10 max + 1 Con mod
    assert derived.speed == 30
    assert derived.proficiency_bonus == 2
    assert derived.passive_perception == 10
    assert derived.hit_dice == "d10"
    assert derived.spellcasting_ability == ""


def test_domain_derived_values_for_wizard() -> None:
    scores = {
        "Strength": 8,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 15,
        "Wisdom": 12,
        "Charisma": 10,
    }
    derived = derive_values(scores, "Wizard", "Goliath", level=1)

    assert derived.armor_class == 12
    assert derived.max_hp == 7  # d6 max + 1 Con mod
    assert derived.speed == 35
    assert derived.spellcasting_ability == "Intelligence"


def test_domain_validate_draft_catches_missing_name() -> None:
    draft = CharacterDraft(
        name="",
        ancestry="Human",
        class_name="Fighter",
        ability_method=AbilityScoreMethod.STANDARD_ARRAY,
        ability_scores={
            "Strength": 10,
            "Dexterity": 10,
            "Constitution": 10,
            "Intelligence": 10,
            "Wisdom": 10,
            "Charisma": 10,
        },
        derived=DerivedValues(armor_class=12, max_hp=10),
    )

    errors = validate_draft(draft)

    assert "Name is required." in errors


def test_domain_validate_draft_catches_invalid_point_buy() -> None:
    draft = CharacterDraft(
        name="Mira",
        ancestry="Human",
        class_name="Fighter",
        ability_method=AbilityScoreMethod.POINT_BUY,
        ability_scores={
            "Strength": 8,
            "Dexterity": 8,
            "Constitution": 8,
            "Intelligence": 8,
            "Wisdom": 8,
            "Charisma": 8,
        },
        derived=DerivedValues(armor_class=12, max_hp=10),
    )

    errors = validate_draft(draft)

    assert "Point buy must spend exactly 27 points." in errors


def test_domain_validate_draft_catches_score_above_twenty() -> None:
    draft = CharacterDraft(
        name="Mira",
        ancestry="Human",
        class_name="Fighter",
        ability_method=AbilityScoreMethod.MANUAL,
        ability_scores={
            "Strength": 21,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 12,
            "Wisdom": 10,
            "Charisma": 8,
        },
        derived=DerivedValues(armor_class=12, max_hp=10),
    )

    errors = validate_draft(draft)

    assert any("20" in error for error in errors)


def test_domain_generate_name_avoids_collisions() -> None:
    rng = random.Random(3)
    existing = {"Mira", "Borin", "Sable"}
    names = {generate_name(existing, rng) for _ in range(20)}

    assert names.isdisjoint(existing)
    assert len(names) > 1


def test_domain_random_concept_returns_a_string() -> None:
    rng = random.Random(1)
    concept = random_concept(rng)

    assert isinstance(concept, str)
    assert len(concept) > 0


def test_domain_build_random_draft_returns_level_one_character() -> None:
    rng = random.Random(42)
    player = Player(id=7, name="Player One", campaign_id=1)

    draft = build_random_draft(set(), [player], rng)

    assert draft.level == 1
    assert draft.name
    assert draft.class_name in [item.value for item in CharacterClass]
    assert draft.ancestry in [item.value for item in CharacterAncestry]
    assert draft.player_id == 7
    assert set(draft.ability_scores) == {
        "Strength",
        "Dexterity",
        "Constitution",
        "Intelligence",
        "Wisdom",
        "Charisma",
    }


def test_domain_ability_modifier_matches_score() -> None:
    assert ability_modifier(10) == 0
    assert ability_modifier(12) == 1
    assert ability_modifier(9) == -1
    assert ability_modifier(20) == 5
    assert ability_modifier(1) == -5


def test_domain_validate_draft_catches_invalid_standard_array() -> None:
    draft = CharacterDraft(
        name="Mira",
        ancestry="Human",
        class_name="Fighter",
        ability_method=AbilityScoreMethod.STANDARD_ARRAY,
        ability_scores={
            "Strength": 15,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 12,
            "Wisdom": 10,
            "Charisma": 9,
        },
        derived=DerivedValues(armor_class=12, max_hp=10),
    )

    errors = validate_draft(draft)

    assert "Standard array must be exactly 15, 14, 13, 12, 10, 8." in errors


def test_domain_validate_draft_catches_invalid_hit_points() -> None:
    draft = CharacterDraft(
        name="Mira",
        ancestry="Human",
        class_name="Fighter",
        ability_method=AbilityScoreMethod.STANDARD_ARRAY,
        ability_scores={
            "Strength": 8,
            "Dexterity": 10,
            "Constitution": 12,
            "Intelligence": 13,
            "Wisdom": 14,
            "Charisma": 15,
        },
        derived=DerivedValues(armor_class=12, max_hp=0),
    )

    errors = validate_draft(draft)

    assert "Maximum hit points must be greater than 0." in errors


def test_domain_validate_draft_catches_unknown_class() -> None:
    draft = CharacterDraft(
        name="Mira",
        ancestry="Human",
        class_name="Gunslinger",
        ability_method=AbilityScoreMethod.STANDARD_ARRAY,
        ability_scores={
            "Strength": 8,
            "Dexterity": 10,
            "Constitution": 12,
            "Intelligence": 13,
            "Wisdom": 14,
            "Charisma": 15,
        },
        derived=DerivedValues(armor_class=12, max_hp=10),
    )

    errors = validate_draft(draft)

    assert any("Unknown class" in error for error in errors)
