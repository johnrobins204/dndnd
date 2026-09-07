from dndnd.intelligence.game_chat import (
    DM_VOICE_PARAMS,
    VOICE_CONFIGS,
    build_adjudicator_prompt,
    build_game_chat_prompt,
    build_game_state_payload,
    build_narrator_prompt,
    build_turn_summary,
    character_include_names,
    strip_preamble,
)
from dndnd.models import (
    Campaign,
    Character,
    Game,
    Quest,
    QuestObjective,
    QuestObjectiveStatus,
    SessionEntry,
    SessionEntryKind,
    SessionRun,
)
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


def test_game_chat_prompt_supports_voice_configs_and_character_json() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(id=2, campaign=campaign, name="Mara", class_name="Fighter")
    game = Game(
        id=3, campaign=campaign, character=character, name="Mara at the archive"
    )
    session_run = SessionRun(id=4, campaign=campaign, game=game, title="Opening scene")
    session_run.entries.append(
        SessionEntry(kind=SessionEntryKind.TABLE_NOTE, content="The bell rings below.")
    )

    prompt = build_game_chat_prompt(
        game=game,
        session_run=session_run,
        voice_key="player_journal",
        user_input="Write this as a recovered page. /character Mara",
        included_characters=[character],
    )

    assert set(VOICE_CONFIGS) == {
        "dm_voice",
        "dm_analysis",
        "player_voice",
        "player_journal",
    }
    assert "Voice target: Player journal article" in prompt
    assert '"name": "Mara"' in prompt
    assert "The bell rings below." in prompt
    assert "Write this as a recovered page. /character Mara" in prompt


def test_character_include_names_parse_slash_references() -> None:
    assert character_include_names("Ask /character Mara\nthen /character Borin") == [
        "Mara",
        "Borin",
    ]


def test_game_state_payload_includes_characters_and_last_action() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(id=2, campaign=campaign, name="Mara", class_name="Fighter")
    game = Game(
        id=3, campaign=campaign, character=character, name="Mara at the archive"
    )
    session_run = SessionRun(id=4, campaign=campaign, game=game, title="Opening scene")
    session_run.entries.append(
        SessionEntry(kind=SessionEntryKind.TABLE_NOTE, content="The bell rings below.")
    )

    payload = build_game_state_payload(
        game=game,
        session_run=session_run,
        user_input="I swing my sword at the guard.",
        included_characters=[character],
    )

    assert payload["last_action"] == "I swing my sword at the guard."
    assert payload["characters"][0]["name"] == "Mara"
    assert payload["included_characters"][0]["name"] == "Mara"
    assert any(
        turn["content"] == "The bell rings below." for turn in payload["recent_turns"]
    )


def test_adjudicator_prompt_demands_bulleted_mechanical_facts() -> None:
    prompt = build_adjudicator_prompt({"last_action": "I swing my sword."})
    assert "logic engine for a tabletop RPG" in prompt
    assert '"last_action": "I swing my sword."' in prompt
    assert "Output ONLY a concise, bulleted list" in prompt
    assert "Do not include preambles" in prompt


def test_narrator_prompt_embeds_mechanical_outcome_and_voice_params() -> None:
    prompt = build_narrator_prompt("- Hit for 6 damage.", DM_VOICE_PARAMS)
    assert "- Hit for 6 damage." in prompt
    assert f"Tone: {DM_VOICE_PARAMS.tone}" in prompt
    assert f"Persona: {DM_VOICE_PARAMS.dm_persona}" in prompt
    assert "Do not mention mechanics, numbers, or dice rolls" in prompt
    assert "Do not include preambles" in prompt


def test_strip_preamble_removes_common_lead_ins() -> None:
    cleaned, preamble = strip_preamble(
        "Here's your response:\n\nThe door creaks open."
    )
    assert cleaned == "The door creaks open."
    assert preamble == "Here's your response:"

    cleaned, preamble = strip_preamble("Here is the analysis: - Partial success")
    assert cleaned == "- Partial success"
    assert preamble == "Here is the analysis:"


def test_strip_preamble_preserves_narrative_with_colons() -> None:
    text = "The guard shouts a warning:\n\nYou dodge aside."
    cleaned, preamble = strip_preamble(text)
    assert cleaned == text
    assert preamble is None


def test_strip_preamble_unwraps_outer_quotes() -> None:
    cleaned, preamble = strip_preamble('"You swing your blade."')
    assert cleaned == "You swing your blade."
    assert preamble is None


def test_turn_summary_counts_chat_inputs_only() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(id=2, campaign=campaign, name="Mara", class_name="Fighter")
    game = Game(
        id=3, campaign=campaign, character=character, name="Mara at the archive"
    )
    session_run = SessionRun(id=4, campaign=campaign, game=game, title="Opening scene")
    session_run.entries.append(
        SessionEntry(kind=SessionEntryKind.CHAT_INPUT, content="First move.")
    )
    session_run.entries.append(
        SessionEntry(kind=SessionEntryKind.CHAT_OUTPUT, content="Narration.")
    )
    session_run.entries.append(
        SessionEntry(kind=SessionEntryKind.TABLE_NOTE, content="DM note.")
    )

    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.turn_number == 2
    assert summary.scene == "Opening scene"
    assert summary.quest_title is None
    assert summary.quest_goal == "No active quest"


def test_turn_summary_uses_first_open_quest_objective() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(id=2, campaign=campaign, name="Mara", class_name="Fighter")
    quest = Quest(id=3, campaign=campaign, title="Recover the Moon Key")
    quest.objectives.append(
        QuestObjective(
            title="Closed lead",
            sort_order=0,
            status=QuestObjectiveStatus.COMPLETE,
        )
    )
    quest.objectives.append(
        QuestObjective(
            title="Find the drowned archive",
            sort_order=1,
            status=QuestObjectiveStatus.OPEN,
        )
    )
    game = Game(id=4, campaign=campaign, character=character, quest=quest, name="Run")
    session_run = SessionRun(id=5, campaign=campaign, game=game, title="Scene")

    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.quest_title == "Recover the Moon Key"
    assert summary.quest_goal == "Find the drowned archive"


def test_turn_summary_falls_back_to_quest_objective_text() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(id=2, campaign=campaign, name="Mara", class_name="Fighter")
    quest = Quest(
        id=3,
        campaign=campaign,
        title="Recover the Moon Key",
        objective="Reach the drowned archive.",
    )
    game = Game(id=4, campaign=campaign, character=character, quest=quest, name="Run")
    session_run = SessionRun(id=5, campaign=campaign, game=game, title="Scene")

    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.quest_title == "Recover the Moon Key"
    assert summary.quest_goal == "Reach the drowned archive."


def test_turn_summary_party_conditions() -> None:
    campaign = Campaign(id=1, name="The Lantern March")
    character = Character(
        id=2,
        campaign=campaign,
        name="Mara",
        class_name="Fighter",
        max_hp=20,
        current_hp=10,
    )
    game = Game(
        id=3, campaign=campaign, character=character, name="Mara at the archive"
    )
    session_run = SessionRun(id=4, campaign=campaign, game=game, title="Scene")

    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.party[0].condition == "Bloodied"

    character.current_hp = 20
    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.party[0].condition == "Healthy"

    character.current_hp = 0
    summary = build_turn_summary(game=game, session_run=session_run)
    assert summary.party[0].condition == "Down"
