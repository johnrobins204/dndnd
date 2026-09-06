from dndnd.app import (
    POINT_BUY_BUDGET,
    build_roll_board,
    generate_ability_scores,
    point_buy_total,
    random_character_draft,
)
from dndnd.models import CharacterAncestry, CharacterClass, CharacterKind, Player


def test_random_character_draft_is_level_one_and_engine_ready() -> None:
    draft = random_character_draft([Player(id=7, name="Player One", campaign_id=1)])

    assert draft["level"] == 1
    assert "-" in draft["name"]
    assert draft["kind"] in [item.value for item in CharacterKind]
    assert draft["ancestry"] in [item.value for item in CharacterAncestry]
    assert draft["class_name"] in [item.value for item in CharacterClass]
    assert set(draft["ability_values"]) == {
        "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"
    }
    assert sorted(draft["ability_values"].values()) == [8, 10, 12, 13, 14, 15]
    assert draft["player_id"] == 7


def test_dice_roll_scores_are_valid_for_4d6_drop_lowest() -> None:
    scores = generate_ability_scores("Dice roll (4d6, drop lowest)")

    assert set(scores) == {
        "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"
    }
    assert all(3 <= score <= 18 for score in scores.values())


def test_roll_board_preserves_landed_scores_and_hides_active_score() -> None:
    board = "\n".join(
        build_roll_board(
            "Dice roll (4d6, drop lowest)", {"Strength": 15}, "Dexterity", 2
        )
    )

    assert "Strength** · **15" in board
    assert "Dexterity** · rolling" in board
    assert "Dexterity** · **" not in board
    assert "Constitution** · waiting" in board


def test_point_buy_uses_the_27_point_budget() -> None:
    standard_point_buy = {
        "Strength": 15, "Dexterity": 14, "Constitution": 13,
        "Intelligence": 12, "Wisdom": 10, "Charisma": 8,
    }

    assert POINT_BUY_BUDGET == 27
    assert point_buy_total(standard_point_buy) == POINT_BUY_BUDGET
