from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from dndnd.models import (
    Alignment,
    CharacterAncestry,
    CharacterClass,
    CharacterKind,
    Player,
)
from dndnd.rules import (
    ANCESTRY_TRAITS,
    BACKGROUND_BONUSES,
    BACKGROUND_OPTIONS,
    CLASS_PRIORITIES,
    HIT_DICE,
    HIT_DIE_SIZES,
    RANDOM_CONCEPTS,
    SPELLCASTING_ABILITIES,
    STARTING_FEATURES,
)

ABILITY_NAMES = [
    "Strength",
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma",
]

POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27
POINT_BUY_MIN_SCORE = 8
POINT_BUY_MAX_SCORE = 15


class AbilityScoreMethod(StrEnum):
    STANDARD_ARRAY = "Standard array"
    DICE_4D6_DROP_LOWEST = "Dice roll (4d6, drop lowest)"
    POINT_BUY = "Point buy final scores"
    MANUAL = "Manual entry"


@dataclass
class DerivedValues:
    armor_class: int = 10
    max_hp: int = 1
    speed: int = 30
    proficiency_bonus: int = 2
    passive_perception: int = 10
    hit_dice: str = ""
    spellcasting_ability: str = ""


@dataclass
class CharacterDraft:
    name: str = ""
    kind: str = "NPC"
    player_id: int | None = None
    ancestry: str = ""
    class_name: str = ""
    level: int = 1
    background: str = ""
    alignment: str = ""
    concept: str = ""
    ability_method: AbilityScoreMethod = AbilityScoreMethod.MANUAL
    ability_scores: dict[str, int] = field(default_factory=dict)
    derived: DerivedValues = field(default_factory=DerivedValues)
    feature_lines: list[str] = field(default_factory=list)
    notes: str = ""


def point_buy_total(scores: dict[str, int]) -> int:
    return sum(POINT_BUY_COSTS.get(score, 999) for score in scores.values())


def proficiency_bonus_for_level(level: int) -> int:
    return 2 + max(0, (level - 1) // 4)


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def _roll_4d6_drop_lowest(rng: random.Random) -> int:
    rolls = sorted(rng.randint(1, 6) for _ in range(4))
    return sum(rolls[1:])


def generate_ability_scores(method: AbilityScoreMethod, rng: random.Random) -> dict[str, int]:
    if method in {
        AbilityScoreMethod.STANDARD_ARRAY,
        AbilityScoreMethod.POINT_BUY,
    }:
        scores = [15, 14, 13, 12, 10, 8]
    elif method == AbilityScoreMethod.DICE_4D6_DROP_LOWEST:
        scores = [_roll_4d6_drop_lowest(rng) for _ in ABILITY_NAMES]
    elif method == AbilityScoreMethod.MANUAL:
        raise ValueError("Manual ability scores must be provided by the UI.")
    else:
        raise ValueError(f"Unknown ability score method: {method}")
    rng.shuffle(scores)
    return dict(zip(ABILITY_NAMES, scores, strict=True))


def assign_scores_by_class(scores: list[int], class_name: str) -> dict[str, int]:
    if class_name not in CLASS_PRIORITIES:
        raise ValueError(f"Unknown class: {class_name}")
    priorities = CLASS_PRIORITIES[class_name]
    if len(scores) != len(priorities):
        raise ValueError(f"Expected {len(priorities)} ability scores, got {len(scores)}")
    sorted_scores = sorted(scores, reverse=True)
    return dict(zip(priorities, sorted_scores, strict=True))


def _apply_bonuses(scores: dict[str, int], bonuses: tuple[tuple[str, int], ...]) -> dict[str, int]:
    updated = dict(scores)
    for ability, bonus in bonuses:
        updated[ability] = min(20, updated.get(ability, 10) + bonus)
    return updated


def apply_ancestry_bonuses(scores: dict[str, int], ancestry: str) -> dict[str, int]:
    if ancestry not in ANCESTRY_TRAITS:
        raise ValueError(f"Unknown ancestry: {ancestry}")
    traits = ANCESTRY_TRAITS[ancestry]
    bonuses = traits.bonuses
    if ancestry == "Human":
        sorted_abilities = sorted(scores, key=lambda ability: scores[ability], reverse=True)
        bonuses = tuple((ability, 1) for ability in sorted_abilities[:3])
    return _apply_bonuses(scores, bonuses)


def apply_background_bonuses(
    scores: dict[str, int], background: str
) -> tuple[dict[str, int], list[str]]:
    if background not in BACKGROUND_BONUSES:
        raise ValueError(f"Unknown background: {background}")
    bonuses = BACKGROUND_BONUSES[background]
    updated = _apply_bonuses(scores, bonuses.bonuses)
    return updated, list(bonuses.proficiencies)


def ancestry_speed(ancestry: str) -> int:
    if ancestry not in ANCESTRY_TRAITS:
        raise ValueError(f"Unknown ancestry: {ancestry}")
    return ANCESTRY_TRAITS[ancestry].speed


def derive_values(
    scores: dict[str, int], class_name: str, ancestry: str, level: int
) -> DerivedValues:
    if class_name not in HIT_DICE:
        raise ValueError(f"Unknown class: {class_name}")
    dexterity_modifier = ability_modifier(scores.get("Dexterity", 10))
    constitution_modifier = ability_modifier(scores.get("Constitution", 10))
    wisdom_modifier = ability_modifier(scores.get("Wisdom", 10))
    return DerivedValues(
        armor_class=10 + dexterity_modifier,
        max_hp=max(1, HIT_DIE_SIZES[class_name] + constitution_modifier),
        speed=ancestry_speed(ancestry),
        proficiency_bonus=proficiency_bonus_for_level(level),
        passive_perception=10 + wisdom_modifier,
        hit_dice=HIT_DICE[class_name],
        spellcasting_ability=SPELLCASTING_ABILITIES.get(class_name, ""),
    )


_NAME_SYLLABLES = {
    "prefixes": [
        "Ael",
        "Bael",
        "Cora",
        "Dra",
        "Eld",
        "Fen",
        "Gor",
        "Hal",
        "Ira",
        "Jor",
        "Kael",
        "Lira",
        "Mira",
        "Nyx",
        "Ori",
        "Pax",
        "Quin",
        "Rae",
        "Syl",
        "Thal",
        "Um",
        "Vex",
        "Wyn",
        "Xar",
        "Ysol",
        "Zep",
    ],
    "roots": [
        "an",
        "ara",
        "bin",
        "cor",
        "dell",
        "en",
        "fyr",
        "gorn",
        "helm",
        "is",
        "jorn",
        "kas",
        "lor",
        "mor",
        "norin",
        "orin",
        "per",
        "quin",
        "ros",
        "stel",
        "torn",
        "umin",
        "vok",
        "wyn",
        "xel",
        "yor",
        "zir",
    ],
    "suffixes": [
        "a",
        "ah",
        "an",
        "as",
        "ek",
        "el",
        "en",
        "er",
        "i",
        "ia",
        "ik",
        "in",
        "is",
        "o",
        "on",
        "or",
        "os",
        "u",
        "um",
        "un",
        "ur",
        "us",
    ],
}


def generate_name(existing_names: set[str], rng: random.Random) -> str:
    existing_normalized = {name.casefold() for name in existing_names}
    for _ in range(100):
        prefix = rng.choice(_NAME_SYLLABLES["prefixes"])
        root = rng.choice(_NAME_SYLLABLES["roots"])
        suffix = rng.choice(_NAME_SYLLABLES["suffixes"])
        name = f"{prefix}{root}{suffix}"
        if name.casefold() not in existing_normalized:
            return name
    raise ValueError("Unable to generate a unique name after 100 attempts.")


def random_concept(rng: random.Random) -> str:
    return rng.choice(RANDOM_CONCEPTS)


def build_random_draft(
    existing_names: set[str],
    players: list[Player],
    rng: random.Random,
) -> CharacterDraft:
    class_name = rng.choice([item.value for item in CharacterClass])
    ancestry = rng.choice([item.value for item in CharacterAncestry])
    background = rng.choice(BACKGROUND_OPTIONS)
    alignment = rng.choice([item.value for item in Alignment])
    kind = rng.choice([item.value for item in CharacterKind])
    player_id = rng.choice([player.id for player in players]) if players else None

    name = generate_name(existing_names, rng)
    concept = random_concept(rng)

    raw_scores = generate_ability_scores(AbilityScoreMethod.DICE_4D6_DROP_LOWEST, rng)
    assigned = assign_scores_by_class(list(raw_scores.values()), class_name)
    assigned = apply_ancestry_bonuses(assigned, ancestry)
    assigned, _ = apply_background_bonuses(assigned, background)
    derived = derive_values(assigned, class_name, ancestry, level=1)

    return CharacterDraft(
        name=name,
        kind=kind,
        player_id=player_id,
        ancestry=ancestry,
        class_name=class_name,
        level=1,
        background=background,
        alignment=alignment,
        concept=concept,
        ability_method=AbilityScoreMethod.DICE_4D6_DROP_LOWEST,
        ability_scores=assigned,
        derived=derived,
        feature_lines=[STARTING_FEATURES[class_name]],
        notes="Randomized draft. Review the choices before finishing the character.",
    )


def validate_draft(draft: CharacterDraft) -> list[str]:
    errors: list[str] = []
    if not draft.name.strip():
        errors.append("Name is required.")
    if draft.ancestry not in ANCESTRY_TRAITS:
        errors.append(f"Unknown ancestry: {draft.ancestry}.")
    if draft.class_name not in CLASS_PRIORITIES:
        errors.append(f"Unknown class: {draft.class_name}.")

    scores = draft.ability_scores
    if set(scores) != set(ABILITY_NAMES):
        errors.append("All six ability scores must be provided.")
    elif not all(1 <= score <= 20 for score in scores.values()):
        errors.append("Ability scores must be between 1 and 20.")
    else:
        if draft.ability_method == AbilityScoreMethod.STANDARD_ARRAY:
            if sorted(scores.values()) != [8, 10, 12, 13, 14, 15]:
                errors.append("Standard array must be exactly 15, 14, 13, 12, 10, 8.")
        elif draft.ability_method == AbilityScoreMethod.DICE_4D6_DROP_LOWEST:
            if not all(3 <= score <= 18 for score in scores.values()):
                errors.append("Rolled scores must be between 3 and 18.")
        elif draft.ability_method == AbilityScoreMethod.POINT_BUY:
            if not all(8 <= score <= 15 for score in scores.values()):
                errors.append("Point-buy scores must be between 8 and 15.")
            if point_buy_total(scores) != POINT_BUY_BUDGET:
                errors.append("Point buy must spend exactly 27 points.")
        elif draft.ability_method == AbilityScoreMethod.MANUAL and not all(
            1 <= score <= 20 for score in scores.values()
        ):
            errors.append("Manual scores must be between 1 and 20.")

        if any(score > 20 for score in scores.values()):
            errors.append("No ability score may exceed 20.")

    if draft.derived.max_hp <= 0:
        errors.append("Maximum hit points must be greater than 0.")
    if not 1 <= draft.derived.armor_class <= 40:
        errors.append("Armor class must be between 1 and 40.")

    return errors
