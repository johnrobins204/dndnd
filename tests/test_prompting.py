from dndnd.prompting import CampaignContext, build_session_prompt


def test_session_prompt_contains_context_and_controls() -> None:
    context = CampaignContext(
        campaign_name="The Lantern March",
        characters=["Mara: human fighter"],
        active_quests=["Recover the moon key"],
    )
    prompt = build_session_prompt(
        context,
        objective="Reach the drowned archive",
        tone="Mysterious",
        pacing="Escalating",
        length="Full session",
    )
    assert "The Lantern March" in prompt
    assert "Mara: human fighter" in prompt
    assert "Tone: Mysterious" in prompt
    assert "Do not decide player actions" in prompt
