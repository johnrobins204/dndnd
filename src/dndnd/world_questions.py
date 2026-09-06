from dataclasses import dataclass
from enum import StrEnum


class WorldStep(StrEnum):
    PREMISE = "premise"
    SCOPE = "scope"
    GEOGRAPHY = "geography"
    HISTORY = "history"
    POWER = "power"
    DAILY_LIFE = "daily_life"
    FANTASTIC = "fantastic"
    STARTING_SITUATION = "starting_situation"


class WorldResponseType(StrEnum):
    TEXT = "text"
    LONG_TEXT = "long_text"
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"


@dataclass(frozen=True)
class WorldQuestion:
    key: str
    step: WorldStep
    prompt: str
    response_type: WorldResponseType
    purpose: str
    target_field: str
    options: tuple[str, ...] = ()
    optional: bool = False
    uncertainty_option: str = "I am not sure yet"
    help_text: str = ""


WORLD_QUESTIONS: tuple[WorldQuestion, ...] = (
    WorldQuestion(
        key="world_name",
        step=WorldStep.PREMISE,
        prompt="What is this world called?",
        response_type=WorldResponseType.TEXT,
        purpose="Give the world a stable identity in the campaign workspace.",
        target_field="world_profile.name",
        help_text="Use a working title if the final name is not known yet.",
    ),
    WorldQuestion(
        key="premise",
        step=WorldStep.PREMISE,
        prompt="What is this world about?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Establish the central premise that guides later questions.",
        target_field="world_profile.premise",
        help_text="A sentence or two is enough. Focus on what makes this world distinct.",
    ),
    WorldQuestion(
        key="mood",
        step=WorldStep.PREMISE,
        prompt="What should the world feel like to play in?",
        response_type=WorldResponseType.SINGLE_CHOICE,
        purpose="Set a creative direction for examples and intelligence suggestions.",
        target_field="world_profile.mood",
        options=(
            "Heroic", "Grim", "Mysterious", "Whimsical", "Political", "Mythic",
            "Horror", "Exploration-focused",
        ),
    ),
    WorldQuestion(
        key="scope",
        step=WorldStep.SCOPE,
        prompt="What part of the world matters first?",
        response_type=WorldResponseType.SINGLE_CHOICE,
        purpose="Limit the first pass to a manageable playable scope.",
        target_field="world_profile.scope",
        options=(
            "One settlement", "One region", "One continent", "Several connected nations",
            "A whole planet", "A planar or multi-world setting",
        ),
    ),
    WorldQuestion(
        key="starting_region",
        step=WorldStep.SCOPE,
        prompt="Where should the first campaign begin?",
        response_type=WorldResponseType.TEXT,
        purpose="Anchor the world in a concrete playable starting point.",
        target_field="world_profile.starting_region",
        help_text="This can be a named place or a placeholder like ‘the northern frontier’.",
    ),
    WorldQuestion(
        key="geography",
        step=WorldStep.GEOGRAPHY,
        prompt="What defines the land, climate, and journey?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Create physical constraints that produce locations and travel choices.",
        target_field="world_profile.geography",
        help_text="Mention one landmark, one danger, and one route if you can.",
    ),
    WorldQuestion(
        key="turning_point",
        step=WorldStep.HISTORY,
        prompt="What happened that still affects the present?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Create history with consequences instead of disconnected lore.",
        target_field="world_history.turning_point",
        help_text="Who benefited, who suffered, and what remains unresolved?",
    ),
    WorldQuestion(
        key="power_holders",
        step=WorldStep.POWER,
        prompt="Who has power, and what do they want?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Establish playable factions, goals, resources, and conflict.",
        target_field="world_factions.initial_factions",
        help_text="Name one group, its public purpose, and its private objective.",
    ),
    WorldQuestion(
        key="everyday_life",
        step=WorldStep.DAILY_LIFE,
        prompt="What is ordinary life like here?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Ground the setting in lived experience and table-ready detail.",
        target_field="world_profile.everyday_life",
        help_text="Think about food, work, family, justice, ritual, and common fears.",
    ),
    WorldQuestion(
        key="fantastic_rule",
        step=WorldStep.FANTASTIC,
        prompt="What is possible here that is impossible elsewhere?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Define the world’s distinctive fantastic rule and its cost.",
        target_field="world_magic.initial_rule",
        help_text="Describe its capability, cost, limitation, and visible consequence.",
    ),
    WorldQuestion(
        key="starting_problem",
        step=WorldStep.STARTING_SITUATION,
        prompt="What is happening when the characters arrive?",
        response_type=WorldResponseType.LONG_TEXT,
        purpose="Ensure the completed world produces an immediate playable situation.",
        target_field="starting_situation.problem",
        help_text="Include visible stakes, hidden stakes, and what changes if nobody acts.",
    ),
)


def questions_for_step(step: WorldStep) -> tuple[WorldQuestion, ...]:
    return tuple(question for question in WORLD_QUESTIONS if question.step == step)


def world_step_order() -> tuple[WorldStep, ...]:
    return tuple(WorldStep)
