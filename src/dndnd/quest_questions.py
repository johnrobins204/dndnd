from dataclasses import dataclass
from enum import StrEnum


class QuestStep(StrEnum):
    HOOK = "hook"
    MOTIVATION = "motivation"
    OPPOSITION = "opposition"
    CHOICE = "choice"
    ESCALATION = "escalation"
    CHAPTERS = "chapters"
    REWARDS = "rewards"
    OPENING = "opening"


class QuestResponseType(StrEnum):
    TEXT = "text"
    LONG_TEXT = "long_text"
    SINGLE_CHOICE = "single_choice"


@dataclass(frozen=True)
class QuestQuestion:
    key: str
    step: QuestStep
    prompt: str
    response_type: QuestResponseType
    purpose: str
    target_field: str
    options: tuple[str, ...] = ()
    uncertainty_option: str = "I am not sure yet"
    help_text: str = ""


QUEST_QUESTIONS: tuple[QuestQuestion, ...] = (
    QuestQuestion(
        "title", QuestStep.HOOK, "What is this quest called?", QuestResponseType.TEXT,
        "Give the quest a stable identity.", "quest.title",
    ),
    QuestQuestion(
        "hook", QuestStep.HOOK, "Why would anyone care about this?", QuestResponseType.LONG_TEXT,
        "Create an invitation grounded in a situation rather than a task.", "quest.hook",
        help_text="Describe the problem, promise, or emotional invitation.",
    ),
    QuestQuestion(
        "objective", QuestStep.MOTIVATION,
        "What does someone want badly enough to act?", QuestResponseType.LONG_TEXT,
        "Establish desire, urgency, and the reason this matters now.", "quest.objective",
    ),
    QuestQuestion(
        "opposition", QuestStep.OPPOSITION,
        "Who or what makes this difficult?", QuestResponseType.LONG_TEXT,
        "Create opposition with a goal and a resource, not a generic villain.", "quest.opposition",
    ),
    QuestQuestion(
        "choice", QuestStep.CHOICE,
        "What meaningful choice should the party face?", QuestResponseType.LONG_TEXT,
        "Protect player agency by defining competing goods or sacrifices.", "quest.choice",
        help_text="Name two paths and what each protects or costs.",
    ),
    QuestQuestion(
        "escalation", QuestStep.ESCALATION,
        "What changes if the party delays or fails?", QuestResponseType.LONG_TEXT,
        "Turn the quest into a living situation with consequences.", "quest.escalation",
    ),
    QuestQuestion(
        "chapters", QuestStep.CHAPTERS,
        "What are the next three playable beats?", QuestResponseType.LONG_TEXT,
        "Create a compact arc of discovery, complication, and confrontation.", "quest.chapters",
        help_text="Use one line per beat; triggers and objectives can be refined later.",
    ),
    QuestQuestion(
        "rewards", QuestStep.REWARDS,
        "What changes for the characters when this is resolved?", QuestResponseType.LONG_TEXT,
        "Make rewards reinforce meaning, relationships, and future opportunity.", "quest.rewards",
    ),
    QuestQuestion(
        "opening", QuestStep.OPENING,
        "What can the DM put in front of the players first?", QuestResponseType.LONG_TEXT,
        "Ensure the quest can begin at the table without missing invention.", "quest.opening",
        help_text="Include a place, an image, an NPC, an actionable problem, and a hidden detail.",
    ),
)


def questions_for_step(step: QuestStep) -> tuple[QuestQuestion, ...]:
    return tuple(question for question in QUEST_QUESTIONS if question.step == step)


def quest_step_order() -> tuple[QuestStep, ...]:
    return tuple(QuestStep)
