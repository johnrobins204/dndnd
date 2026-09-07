from sqlalchemy import select

from dndnd.config import Settings
from dndnd.db import create_database_engine, initialize_database, session_scope
from dndnd.models import (
    Campaign,
    Character,
    CharacterJournalEntry,
    CharacterKind,
    CharacterSheet,
    InventoryItem,
    Item,
    ItemKind,
    Quest,
    QuestChapter,
    QuestCharacter,
    QuestItem,
    QuestObjective,
    QuestReward,
    QuestStatus,
    QuestTrigger,
    QuestTriggerType,
    SessionEntry,
    SessionEntryKind,
    SessionRun,
    SessionRunStatus,
    WorldDraft,
    WorldDraftChange,
    WorldFaction,
    WorldHistoryEvent,
    WorldMagicRule,
    WorldProfile,
    WorldStartingSituation,
)


def test_campaign_and_character_are_persisted() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        campaign.characters.append(
            Character(
                name="Mara",
                kind=CharacterKind.PLAYER_CHARACTER,
                max_hp=12,
                current_hp=12,
            )
        )
        session.add(campaign)
    with session_scope(engine) as session:
        saved = session.scalar(select(Campaign))
        assert saved is not None
        assert saved.characters[0].name == "Mara"


def test_character_and_quest_graph_are_persisted() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        character = Character(name="Mara", kind=CharacterKind.PLAYER_CHARACTER)
        character.sheet = CharacterSheet(background="Sailor", proficiency_bonus=3)
        character.journal_entries.append(
            CharacterJournalEntry(
                title="The locked lighthouse", body="Mara remembers the signal."
            )
        )
        item = Item(name="Moon Key", kind=ItemKind.QUEST, is_unique=True)
        character.inventory.append(InventoryItem(item=item, quantity=1, attuned=True))
        quest = Quest(title="Open the drowned archive", status=QuestStatus.ACTIVE)
        chapter = QuestChapter(title="The descent", sort_order=1)
        chapter.objectives.append(
            QuestObjective(title="Find the submerged entrance", quest=quest)
        )
        chapter.triggers.append(
            QuestTrigger(
                name="Key recovered",
                trigger_type=QuestTriggerType.ITEM,
                condition="The Moon Key is in a character inventory",
                effect="Unlock the archive",
                quest=quest,
            )
        )
        chapter.rewards.append(
            QuestReward(title="Archive knowledge", experience_points=100, quest=quest)
        )
        quest.chapters.append(chapter)
        quest.item_links.append(QuestItem(item=item, role="Required"))
        quest.npc_links.append(QuestCharacter(character=character, role="Protagonist"))
        campaign.characters.append(character)
        campaign.items.append(item)
        campaign.quests.append(quest)
        session.add(campaign)

    with session_scope(engine) as session:
        saved = session.scalar(select(Quest))
        assert saved is not None
        assert saved.chapters[0].objectives[0].title == "Find the submerged entrance"
        assert saved.chapters[0].triggers[0].trigger_type == QuestTriggerType.ITEM
        assert saved.item_links[0].item.name == "Moon Key"
        assert saved.npc_links[0].character.sheet is not None
        assert (
            saved.npc_links[0].character.journal_entries[0].title
            == "The locked lighthouse"
        )


def test_session_run_preserves_table_transcript() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        run = SessionRun(
            title="The drowned archive",
            status=SessionRunStatus.ACTIVE,
            current_scene="The bell chamber",
        )
        run.entries.extend(
            [
                SessionEntry(kind=SessionEntryKind.SCENE, content="The bell chamber"),
                SessionEntry(
                    kind=SessionEntryKind.NARRATION, content="The tide withdraws."
                ),
                SessionEntry(
                    kind=SessionEntryKind.DM_NOTE,
                    content="The sigil is warm.",
                    is_dm_only=True,
                ),
            ]
        )
        campaign.session_runs.append(run)
        session.add(campaign)

    with session_scope(engine) as session:
        saved = session.scalar(select(SessionRun))
        assert saved is not None
        assert saved.status == SessionRunStatus.ACTIVE
        assert saved.current_scene == "The bell chamber"
        assert [entry.kind for entry in saved.entries] == [
            SessionEntryKind.SCENE,
            SessionEntryKind.NARRATION,
            SessionEntryKind.DM_NOTE,
        ]
        assert saved.entries[-1].is_dm_only is True


def test_accepted_world_profile_persists_canonical_graph() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        profile = WorldProfile(
            name="The Lantern March",
            premise="A frontier where old magic is waking.",
            mood="Mysterious",
            scope="One region",
            starting_region="The drowned coast",
        )
        profile.history_events.append(
            WorldHistoryEvent(
                title="The turning point", description="The sea withdrew."
            )
        )
        profile.factions.append(
            WorldFaction(
                name="The Salt Compact", public_purpose="Control the trade roads."
            )
        )
        profile.magic_rules.append(
            WorldMagicRule(
                name="The tide remembers", capability="Water preserves memories."
            )
        )
        profile.starting_situations.append(
            WorldStartingSituation(
                title="The first bell", problem="A warning bell rings below the tide."
            )
        )
        campaign.world_profile = profile
        session.add(campaign)

    with session_scope(engine) as session:
        saved = session.scalar(select(WorldProfile))
        assert saved is not None
        assert saved.premise == "A frontier where old magic is waking."
        assert saved.history_events[0].title == "The turning point"
        assert saved.factions[0].name == "The Salt Compact"
        assert saved.magic_rules[0].capability == "Water preserves memories."
        assert (
            saved.starting_situations[0].problem
            == "A warning bell rings below the tide."
        )


def test_existing_world_change_stays_a_draft_until_accepted() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        campaign_change = WorldDraftChange(
            campaign_id=1,
            change_type="Faction",
            title="The Salt Compact",
            placement="The drowned coast",
            details="A trade guild controls the surviving salt roads.",
            visibility="Local knowledge",
            intended_output="Quest hook",
        )
        campaign.world_profile = WorldProfile(name="The Lantern March")
        session.add(campaign)
        session.add(campaign_change)

    with session_scope(engine) as session:
        saved = session.scalar(select(WorldDraftChange))
        assert saved is not None
        assert saved.status == "Draft"
        assert saved.source == "User"
        assert saved.title == "The Salt Compact"


def test_world_builder_draft_recovers_answers_and_step() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = Campaign(name="The Lantern March")
        session.add(campaign)
        session.flush()
        session.add(
            WorldDraft(
                campaign_id=campaign.id,
                answers_json='{"world_name": "The Lantern March", "premise": "A waking frontier."}',
                current_step=1,
                is_reviewing=False,
            )
        )

    with session_scope(engine) as session:
        saved = session.scalar(select(WorldDraft))
        assert saved is not None
        assert '"world_name": "The Lantern March"' in saved.answers_json
        assert saved.current_step == 1
        assert saved.is_reviewing is False


def test_database_initialization_adds_session_game_links_to_existing_sqlite() -> None:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE session_runs ("
            "id INTEGER PRIMARY KEY, "
            "campaign_id INTEGER NOT NULL, "
            "title VARCHAR(160) NOT NULL, "
            "session_number INTEGER, "
            "status VARCHAR(30) NOT NULL, "
            "current_scene VARCHAR(160) NOT NULL, "
            "summary TEXT NOT NULL, "
            "started_at DATETIME, "
            "ended_at DATETIME, "
            "created_at DATETIME NOT NULL"
            ")"
        )

    initialize_database(engine)

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(session_runs)")
        }

    assert "character_id" in columns
    assert "game_id" in columns
    assert "quest_id" in columns
