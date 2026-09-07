from dndnd.config import Settings
from dndnd.data.repositories.campaigns import (
    STARTER_CAMPAIGN_NAME,
    STARTER_CAMPAIGN_SUMMARY,
    CampaignRepository,
)
from dndnd.data.repositories.characters import CharacterRepository
from dndnd.data.repositories.games import GameRepository
from dndnd.data.repositories.quests import QuestRepository
from dndnd.data.repositories.sessions import SessionRepository
from dndnd.data.repositories.worlds import WorldRepository
from dndnd.db import create_database_engine, initialize_database, session_scope
from dndnd.domain.characters import (
    AbilityScoreMethod,
    CharacterDraft,
    DerivedValues,
)
from dndnd.models import (
    Campaign,
    Character,
    Game,
    GameStatus,
    Item,
    Location,
    Player,
    Quest,
    QuestChapter,
    QuestObjective,
    QuestStatus,
    SessionEntry,
    SessionEntryKind,
    SessionRun,
    SessionRunStatus,
    WorldDraftChange,
)


def test_campaign_repository_seeds_starter_campaign_once() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = CampaignRepository()

    with session_scope(engine) as session:
        first = repository.ensure_starter(session)
        session.commit()
        second = repository.ensure_starter(session)

        assert first.id == second.id
        assert second.name == STARTER_CAMPAIGN_NAME
        assert second.summary == STARTER_CAMPAIGN_SUMMARY
        assert len(repository.list_all(session)) == 1


def test_character_repository_lists_campaign_party_data_in_name_order() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = CharacterRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        other_campaign = Campaign(name="Elsewhere")
        session.add_all([campaign, other_campaign])
        session.flush()
        session.add_all(
            [
                Player(campaign_id=campaign.id, name="Zara"),
                Player(campaign_id=campaign.id, name="Ansel"),
                Player(campaign_id=other_campaign.id, name="Other"),
                Character(campaign_id=campaign.id, name="Mira"),
                Character(campaign_id=campaign.id, name="Borin"),
                Character(campaign_id=other_campaign.id, name="Other"),
                Item(campaign_id=campaign.id, name="Moon Key"),
                Item(campaign_id=campaign.id, name="Amber Map"),
                Item(campaign_id=other_campaign.id, name="Other"),
            ]
        )

    with session_scope(engine) as session:
        assert [player.name for player in repository.list_players_for_campaign(session, 1)] == [
            "Ansel",
            "Zara",
        ]
        assert [character.name for character in repository.list_for_campaign(session, 1)] == [
            "Borin",
            "Mira",
        ]
        assert [item.name for item in repository.list_items_for_campaign(session, 1)] == [
            "Amber Map",
            "Moon Key",
        ]


def test_game_repository_creates_and_lists_active_character_games() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = GameRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        other_campaign = Campaign(name="Elsewhere")
        character = Character(name="Mira", campaign=campaign)
        companion = Character(name="Sable", campaign=campaign)
        quest = Quest(title="Open the drowned archive", campaign=campaign)
        other_character = Character(name="Borin", campaign=other_campaign)
        session.add_all([campaign, other_campaign, character, companion, quest, other_character])
        session.flush()
        game = repository.create(
            session,
            name="Mira and the drowned archive",
            campaign_id=campaign.id,
            character_id=character.id,
            character_ids=[character.id, companion.id],
            quest_id=quest.id,
        )
        inactive = Game(
            name="Closed table",
            campaign=campaign,
            character=character,
            status=GameStatus.COMPLETE,
        )
        session.add(inactive)

    with session_scope(engine) as session:
        active_games = repository.list_active(session)
        loaded_game = repository.get_active(session, game.id)
        options = repository.list_character_options(session)
        campaign_options = repository.list_character_options_for_campaign(session, 1)
        quest_options = repository.list_quest_options_for_campaign(session, 1)

    assert [item.name for item in active_games] == ["Mira and the drowned archive"]
    assert active_games[0].id == game.id
    assert active_games[0].campaign.name == "The Lantern March"
    assert active_games[0].character.name == "Mira"
    assert loaded_game is not None
    assert loaded_game.name == "Mira and the drowned archive"
    assert loaded_game.quest is not None
    assert loaded_game.quest.title == "Open the drowned archive"
    assert [link.character.name for link in loaded_game.character_links] == [
        "Mira",
        "Sable",
    ]
    assert [option.label for option in options] == [
        "Elsewhere · Borin",
        "The Lantern March · Mira",
        "The Lantern March · Sable",
    ]
    assert [option.label for option in campaign_options] == ["Mira", "Sable"]
    assert [option.label for option in quest_options] == ["Open the drowned archive"]

    with session_scope(engine) as session:
        found = CharacterRepository().find_by_name_for_campaign(session, 1, "mira")

    assert found is not None
    assert found.name == "Mira"


def test_quest_repository_lists_builder_data_for_one_campaign() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = QuestRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        other_campaign = Campaign(name="Elsewhere")
        session.add_all([campaign, other_campaign])
        session.flush()
        quest = Quest(campaign_id=campaign.id, title="Open the drowned archive")
        quest.chapters.append(QuestChapter(title="The descent"))
        quest.objectives.append(QuestObjective(title="Find the submerged entrance"))
        session.add_all(
            [
                quest,
                Quest(
                    campaign_id=campaign.id,
                    title="Answer the bell",
                    status=QuestStatus.ACTIVE,
                ),
                Quest(campaign_id=other_campaign.id, title="Other"),
                Item(campaign_id=campaign.id, name="Moon Key"),
                Character(campaign_id=campaign.id, name="Mira"),
                Location(campaign_id=campaign.id, name="Archive Steps"),
                Item(campaign_id=other_campaign.id, name="Other"),
                Character(campaign_id=other_campaign.id, name="Other"),
                Location(campaign_id=other_campaign.id, name="Other"),
            ]
        )
        session.flush()
        quest_id = quest.id

    with session_scope(engine) as session:
        assert [quest.title for quest in repository.list_for_campaign(session, 1)] == [
            "Answer the bell",
            "Open the drowned archive",
        ]
        assert [item.name for item in repository.list_items_for_campaign(session, 1)] == [
            "Moon Key"
        ]
        assert [
            character.name for character in repository.list_characters_for_campaign(session, 1)
        ] == ["Mira"]
        assert [
            location.name for location in repository.list_locations_for_campaign(session, 1)
        ] == ["Archive Steps"]
        loaded = repository.get_builder(session, quest_id)
        assert loaded is not None
        assert loaded.chapters[0].title == "The descent"
        assert loaded.objectives[0].title == "Find the submerged entrance"


def test_world_repository_lists_locations_and_draft_changes_for_one_campaign() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = WorldRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        other_campaign = Campaign(name="Elsewhere")
        session.add_all([campaign, other_campaign])
        session.flush()
        session.add_all(
            [
                Location(campaign_id=campaign.id, name="Bell Harbor"),
                Location(campaign_id=campaign.id, name="Archive Steps"),
                Location(campaign_id=other_campaign.id, name="Other"),
                WorldDraftChange(campaign_id=campaign.id, change_type="Faction", title="First"),
                WorldDraftChange(campaign_id=campaign.id, change_type="Location", title="Second"),
                WorldDraftChange(
                    campaign_id=other_campaign.id,
                    change_type="Location",
                    title="Other",
                ),
            ]
        )

    with session_scope(engine) as session:
        assert [
            location.name for location in repository.list_locations_for_campaign(session, 1)
        ] == [
            "Archive Steps",
            "Bell Harbor",
        ]
        assert {
            change.title for change in repository.list_draft_changes_for_campaign(session, 1)
        } == {"First", "Second"}


def test_character_repository_exists_name_in_campaign_is_case_insensitive() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = CharacterRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        session.add(campaign)
        session.flush()
        session.add(Character(campaign_id=campaign.id, name="Mira"))

    with session_scope(engine) as session:
        assert repository.exists_name_in_campaign(session, campaign.id, "Mira")
        assert repository.exists_name_in_campaign(session, campaign.id, "mira")
        assert not repository.exists_name_in_campaign(session, campaign.id, "Borin")


def test_character_repository_create_from_draft_persists_full_sheet() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = CharacterRepository()

    draft = CharacterDraft(
        name="Mira",
        kind="Player character",
        ancestry="Elf",
        class_name="Wizard",
        level=1,
        background="Sage",
        alignment="True Neutral",
        concept="Seeks a lost promise beneath an ordinary life.",
        ability_method=AbilityScoreMethod.STANDARD_ARRAY,
        ability_scores={
            "Strength": 8,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 15,
            "Wisdom": 12,
            "Charisma": 10,
        },
        derived=DerivedValues(
            armor_class=12,
            max_hp=7,
            speed=30,
            proficiency_bonus=2,
            passive_perception=11,
            hit_dice="d6",
            spellcasting_ability="Intelligence",
        ),
        feature_lines=["Spellbook | Prepare a studied repertoire"],
        notes="Test draft.",
    )

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        session.add(campaign)
        session.flush()
        character = repository.create_from_draft(session, campaign.id, draft)
        session.commit()
        character_id = character.id

    with session_scope(engine) as session:
        loaded = repository.get_workspace(session, character_id)
        assert loaded is not None
        assert loaded.name == "Mira"
        assert loaded.ancestry == "Elf"
        assert loaded.class_name == "Wizard"
        assert loaded.max_hp == 7
        assert loaded.sheet is not None
        assert loaded.sheet.ability_score_method == AbilityScoreMethod.STANDARD_ARRAY
        assert loaded.sheet.spellcasting_ability == "Intelligence"
        assert len(loaded.abilities) == 6
        assert loaded.abilities[0].modifier == (loaded.abilities[0].score - 10) // 2
        assert len(loaded.features) == 1
        assert loaded.features[0].name == "Spellbook"


def test_session_repository_eager_loads_transcript_entries() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = SessionRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        run = SessionRun(campaign=campaign, title="The drowned archive")
        run.entries.append(SessionEntry(kind=SessionEntryKind.SCENE, content="The bell chamber"))
        session.add(campaign)
        session.flush()
        campaign_id = campaign.id
        run_id = run.id

    with session_scope(engine) as session:
        loaded_runs = repository.list_for_campaign(session, campaign_id)
        loaded_run = repository.get(session, run_id)

    assert [entry.content for entry in loaded_runs[0].entries] == ["The bell chamber"]
    assert loaded_run is not None
    assert [entry.kind for entry in loaded_run.entries] == [SessionEntryKind.SCENE]


def test_session_repository_reports_character_and_quest_games() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = SessionRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        character = Character(name="Mira", campaign=campaign)
        quest = Quest(title="Open the drowned archive", campaign=campaign)
        character_run = SessionRun(
            campaign=campaign,
            character=character,
            title="Mira at the bell tower",
            status=SessionRunStatus.ACTIVE,
        )
        character_run.entries.append(
            SessionEntry(kind=SessionEntryKind.SCENE, content="The bell tower")
        )
        quest_run = SessionRun(campaign=campaign, quest=quest, title="The descent")
        quest_run.entries.extend(
            [
                SessionEntry(kind=SessionEntryKind.SCENE, content="The stair opens"),
                SessionEntry(kind=SessionEntryKind.TABLE_NOTE, content="Mark the tide"),
            ]
        )
        session.add(campaign)
        session.flush()
        campaign_id = campaign.id

    with session_scope(engine) as session:
        games = repository.list_games_for_campaign(session, campaign_id)
        active_runs = repository.list_active_for_campaign(session, campaign_id)

    assert [game.key for game in games] == ["character:1", "quest:1"]
    assert games[0].name == "Mira"
    assert games[0].status == "Running"
    assert games[0].session_count == 1
    assert games[0].turn_count == 1
    assert games[0].active_session_title == "Mira at the bell tower"
    assert games[1].name == "Open the drowned archive"
    assert games[1].session_count == 1
    assert games[1].turn_count == 2
    assert [run.title for run in active_runs] == ["Mira at the bell tower"]


def test_session_repository_creates_or_resumes_active_game_session() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    repository = SessionRepository()

    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        character = Character(name="Mira", campaign=campaign)
        game = Game(name="Mira at the archive", campaign=campaign, character=character)
        session.add(campaign)
        session.flush()
        first = repository.get_or_create_active_for_game(session, game)
        second = repository.get_or_create_active_for_game(session, game)

        assert first.id == second.id
        assert second.status == SessionRunStatus.ACTIVE
        assert second.game_id == game.id
        assert second.character_id == character.id
