from dndnd.prompting import WORLD_GUIDANCE_MODES, build_world_guidance_prompt
from dndnd.world_questions import (
    WORLD_QUESTIONS,
    WorldStep,
    questions_for_step,
    world_step_order,
)


def test_world_creation_has_fixed_eight_step_order() -> None:
    assert world_step_order() == (
        WorldStep.PREMISE,
        WorldStep.SCOPE,
        WorldStep.GEOGRAPHY,
        WorldStep.HISTORY,
        WorldStep.POWER,
        WorldStep.DAILY_LIFE,
        WorldStep.FANTASTIC,
        WorldStep.STARTING_SITUATION,
    )
    assert {question.step for question in WORLD_QUESTIONS} == set(world_step_order())


def test_each_question_has_a_purpose_and_model_target() -> None:
    assert WORLD_QUESTIONS
    assert all(question.purpose for question in WORLD_QUESTIONS)
    assert all(question.target_field for question in WORLD_QUESTIONS)
    assert all(question.uncertainty_option for question in WORLD_QUESTIONS)


def test_step_questions_are_grouped_without_cross_step_leakage() -> None:
    premise_questions = questions_for_step(WorldStep.PREMISE)
    assert premise_questions
    assert all(question.step is WorldStep.PREMISE for question in premise_questions)
    assert any(question.key == "premise" for question in premise_questions)
    assert not any(question.key == "starting_problem" for question in premise_questions)


def test_world_guidance_prompt_is_bounded_and_draft_only() -> None:
    assert WORLD_GUIDANCE_MODES == ("Clarify", "Expand", "Connect", "Challenge")
    prompt = build_world_guidance_prompt(
        mode="Challenge",
        step_name="Geography",
        answers={"geography": "A mountain range isolates the coast."},
    )

    assert "Current fixed step: Geography" in prompt
    assert "one contradiction" in prompt
    assert "Do not write canonical records" in prompt
