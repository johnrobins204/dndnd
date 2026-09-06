from dndnd.quest_questions import (
    QUEST_QUESTIONS,
    QuestStep,
    quest_step_order,
    questions_for_step,
)


def test_quest_creation_has_fixed_eight_step_order() -> None:
    assert quest_step_order() == (
        QuestStep.HOOK,
        QuestStep.MOTIVATION,
        QuestStep.OPPOSITION,
        QuestStep.CHOICE,
        QuestStep.ESCALATION,
        QuestStep.CHAPTERS,
        QuestStep.REWARDS,
        QuestStep.OPENING,
    )
    assert {question.step for question in QUEST_QUESTIONS} == set(quest_step_order())


def test_each_quest_question_has_purpose_and_target() -> None:
    assert QUEST_QUESTIONS
    assert all(question.purpose for question in QUEST_QUESTIONS)
    assert all(question.target_field for question in QUEST_QUESTIONS)
    assert all(question.uncertainty_option for question in QUEST_QUESTIONS)


def test_quest_questions_are_grouped_by_decision() -> None:
    choice_questions = questions_for_step(QuestStep.CHOICE)
    assert len(choice_questions) == 1
    assert choice_questions[0].key == "choice"
    assert questions_for_step(QuestStep.OPENING)[0].key == "opening"
