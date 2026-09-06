from dndnd.world_checks import WorldCheck
from dndnd.world_export import build_world_brief


def test_world_brief_contains_core_sections_and_checks() -> None:
    brief = build_world_brief(
        {
            "world_name": "The Lantern March",
            "premise": "A frontier where old magic wakes.",
            "starting_problem": "A bell rings beneath the tide.",
        },
        [WorldCheck("ready", "No obvious checks are waiting.")],
    )

    assert "# The Lantern March" in brief
    assert "## Premise" in brief
    assert "A bell rings beneath the tide." in brief
    assert "**Ready:**" in brief
