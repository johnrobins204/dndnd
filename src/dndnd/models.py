from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CharacterKind(StrEnum):
    PLAYER_CHARACTER = "Player character"
    NPC = "NPC"


class CharacterClass(StrEnum):
    BARBARIAN = "Barbarian"
    BARD = "Bard"
    CLERIC = "Cleric"
    DRUID = "Druid"
    FIGHTER = "Fighter"
    MONK = "Monk"
    PALADIN = "Paladin"
    RANGER = "Ranger"
    ROGUE = "Rogue"
    SORCERER = "Sorcerer"
    WARLOCK = "Warlock"
    WIZARD = "Wizard"


class CharacterAncestry(StrEnum):
    AASIMAR = "Aasimar"
    DRAGONBORN = "Dragonborn"
    DWARF = "Dwarf"
    ELF = "Elf"
    GNOME = "Gnome"
    GOLIATH = "Goliath"
    HALFLING = "Halfling"
    HUMAN = "Human"
    ORC = "Orc"
    TIEFLING = "Tiefling"


class Alignment(StrEnum):
    LAWFUL_GOOD = "Lawful Good"
    NEUTRAL_GOOD = "Neutral Good"
    CHAOTIC_GOOD = "Chaotic Good"
    LAWFUL_NEUTRAL = "Lawful Neutral"
    TRUE_NEUTRAL = "True Neutral"
    CHAOTIC_NEUTRAL = "Chaotic Neutral"
    LAWFUL_EVIL = "Lawful Evil"
    NEUTRAL_EVIL = "Neutral Evil"
    CHAOTIC_EVIL = "Chaotic Evil"


class QuestStatus(StrEnum):
    RUMOR = "Rumor"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    FAILED = "Failed"


class QuestChapterStatus(StrEnum):
    LOCKED = "Locked"
    AVAILABLE = "Available"
    ACTIVE = "Active"
    COMPLETED = "Completed"


class QuestObjectiveStatus(StrEnum):
    HIDDEN = "Hidden"
    OPEN = "Open"
    COMPLETE = "Complete"
    FAILED = "Failed"


class QuestTriggerType(StrEnum):
    MANUAL = "Manual"
    LOCATION = "Location"
    JOURNAL = "Journal"
    OBJECTIVE = "Objective"
    ITEM = "Item"
    NPC = "NPC"
    COMBAT = "Combat"


class ItemKind(StrEnum):
    GEAR = "Gear"
    CONSUMABLE = "Consumable"
    WEAPON = "Weapon"
    ARMOR = "Armor"
    QUEST = "Quest item"
    TREASURE = "Treasure"


class JournalEntryKind(StrEnum):
    MEMORY = "Memory"
    SECRET = "Secret"
    RELATIONSHIP = "Relationship"
    GOAL = "Goal"
    NOTE = "Note"


class SessionRunStatus(StrEnum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETE = "Complete"


class GameStatus(StrEnum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETE = "Complete"


class SessionEntryKind(StrEnum):
    SCENE = "Scene"
    NARRATION = "Narration"
    DM_NOTE = "DM note"
    TABLE_NOTE = "Table note"
    CHAT_INPUT = "Chat input"
    CHAT_OUTPUT = "Chat output"
    SYSTEM = "System"


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    system: Mapped[str] = mapped_column(String(80), default="D&D 5e (2024)")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    players: Mapped[list["Player"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    locations: Mapped[list["Location"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    quests: Mapped[list["Quest"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    encounters: Mapped[list["Encounter"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    items: Mapped[list["Item"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    maps: Mapped[list["CampaignMap"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    session_runs: Mapped[list["SessionRun"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    games: Mapped[list["Game"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    world_profile: Mapped["WorldProfile | None"] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", uselist=False
    )


class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str] = mapped_column(Text, default="")
    campaign: Mapped[Campaign] = relationship(back_populates="players")
    characters: Mapped[list["Character"]] = relationship(back_populates="player")


class Character(Base):
    __tablename__ = "characters"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(30), default=CharacterKind.NPC)
    ancestry: Mapped[str] = mapped_column(String(80), default="")
    class_name: Mapped[str] = mapped_column(String(80), default="")
    level: Mapped[int] = mapped_column(default=1)
    armor_class: Mapped[int] = mapped_column(default=10)
    max_hp: Mapped[int] = mapped_column(default=1)
    current_hp: Mapped[int] = mapped_column(default=1)
    notes: Mapped[str] = mapped_column(Text, default="")
    campaign: Mapped[Campaign] = relationship(back_populates="characters")
    player: Mapped[Player | None] = relationship(back_populates="characters")
    sheet: Mapped["CharacterSheet | None"] = relationship(
        back_populates="character", cascade="all, delete-orphan", uselist=False
    )
    abilities: Mapped[list["CharacterAbility"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    skills: Mapped[list["CharacterSkill"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    features: Mapped[list["CharacterFeature"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    journal_entries: Mapped[list["CharacterJournalEntry"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    inventory: Mapped[list["InventoryItem"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    quest_links: Mapped[list["QuestCharacter"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    games: Mapped[list["Game"]] = relationship(back_populates="character")
    game_links: Mapped[list["GameCharacter"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    session_runs: Mapped[list["SessionRun"]] = relationship(back_populates="character")


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    environment: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    secrets: Mapped[str] = mapped_column(Text, default="")
    campaign: Mapped[Campaign] = relationship(back_populates="locations")


class Quest(Base):
    __tablename__ = "quests"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default=QuestStatus.RUMOR)
    hook: Mapped[str] = mapped_column(Text, default="")
    objective: Mapped[str] = mapped_column(Text, default="")
    reward: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    campaign: Mapped[Campaign] = relationship(back_populates="quests")
    chapters: Mapped[list["QuestChapter"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
        order_by="QuestChapter.sort_order",
    )
    objectives: Mapped[list["QuestObjective"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
        order_by="QuestObjective.sort_order",
    )
    triggers: Mapped[list["QuestTrigger"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )
    rewards: Mapped[list["QuestReward"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )
    map_links: Mapped[list["QuestMap"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )
    item_links: Mapped[list["QuestItem"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )
    npc_links: Mapped[list["QuestCharacter"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )
    table_games: Mapped[list["Game"]] = relationship(back_populates="quest")
    session_runs: Mapped[list["SessionRun"]] = relationship(back_populates="quest")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    body: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(240), default="")
    campaign: Mapped[Campaign] = relationship(back_populates="journal_entries")


class Encounter(Base):
    __tablename__ = "encounters"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    round_number: Mapped[int] = mapped_column(default=1)
    active_turn: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    campaign: Mapped[Campaign] = relationship(back_populates="encounters")
    combatants: Mapped[list["Combatant"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )


class Combatant(Base):
    __tablename__ = "combatants"
    id: Mapped[int] = mapped_column(primary_key=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    initiative: Mapped[int] = mapped_column(default=0)
    armor_class: Mapped[int] = mapped_column(default=10)
    max_hp: Mapped[int] = mapped_column(default=1)
    current_hp: Mapped[int] = mapped_column(default=1)
    conditions: Mapped[str] = mapped_column(String(240), default="")
    encounter: Mapped[Encounter] = relationship(back_populates="combatants")


class CharacterSheet(Base):
    """Rules-facing state kept separate so legacy character rows remain compatible."""

    __tablename__ = "character_sheets"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), unique=True
    )
    background: Mapped[str] = mapped_column(String(120), default="")
    alignment: Mapped[str] = mapped_column(String(40), default="")
    experience_points: Mapped[int] = mapped_column(Integer, default=0)
    temporary_hp: Mapped[int] = mapped_column(Integer, default=0)
    hit_dice: Mapped[str] = mapped_column(String(30), default="")
    speed: Mapped[int] = mapped_column(Integer, default=30)
    proficiency_bonus: Mapped[int] = mapped_column(Integer, default=2)
    passive_perception: Mapped[int] = mapped_column(Integer, default=10)
    inspiration: Mapped[bool] = mapped_column(Boolean, default=False)
    death_save_successes: Mapped[int] = mapped_column(Integer, default=0)
    death_save_failures: Mapped[int] = mapped_column(Integer, default=0)
    spellcasting_ability: Mapped[str] = mapped_column(String(30), default="")
    spell_save_dc: Mapped[int | None] = mapped_column(Integer)
    spell_attack_bonus: Mapped[int | None] = mapped_column(Integer)
    ability_score_method: Mapped[str] = mapped_column(String(60), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    character: Mapped[Character] = relationship(back_populates="sheet")


class CharacterAbility(Base):
    __tablename__ = "character_abilities"
    __table_args__ = (UniqueConstraint("character_id", "ability_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    ability_name: Mapped[str] = mapped_column(String(30))
    score: Mapped[int] = mapped_column(Integer, default=10)
    modifier: Mapped[int] = mapped_column(Integer, default=0)
    save_proficient: Mapped[bool] = mapped_column(Boolean, default=False)
    save_bonus: Mapped[int] = mapped_column(Integer, default=0)
    character: Mapped[Character] = relationship(back_populates="abilities")


class CharacterSkill(Base):
    __tablename__ = "character_skills"
    __table_args__ = (UniqueConstraint("character_id", "skill_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    skill_name: Mapped[str] = mapped_column(String(60))
    ability_name: Mapped[str] = mapped_column(String(30))
    proficiency_rank: Mapped[int] = mapped_column(Integer, default=0)
    bonus: Mapped[int] = mapped_column(Integer, default=0)
    character: Mapped[Character] = relationship(back_populates="skills")


class CharacterFeature(Base):
    __tablename__ = "character_features"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60), default="Feature")
    source: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    uses_max: Mapped[int | None] = mapped_column(Integer)
    uses_remaining: Mapped[int | None] = mapped_column(Integer)
    recharge: Mapped[str] = mapped_column(String(60), default="")
    character: Mapped[Character] = relationship(back_populates="features")


class CharacterJournalEntry(Base):
    __tablename__ = "character_journal_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(40), default=JournalEntryKind.NOTE)
    body: Mapped[str] = mapped_column(Text)
    session_number: Mapped[int | None] = mapped_column(Integer)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[str] = mapped_column(String(240), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    character: Mapped[Character] = relationship(back_populates="journal_entries")


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(40), default=ItemKind.GEAR)
    description: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[float | None] = mapped_column(Float)
    value_gp: Mapped[int | None] = mapped_column(Integer)
    rarity: Mapped[str] = mapped_column(String(40), default="")
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    campaign: Mapped[Campaign] = relationship(back_populates="items")
    inventory_entries: Mapped[list["InventoryItem"]] = relationship(back_populates="item")
    quest_links: Mapped[list["QuestItem"]] = relationship(back_populates="item")
    rewards: Mapped[list["QuestReward"]] = relationship(back_populates="item")


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"))
    custom_name: Mapped[str] = mapped_column(String(160), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    attuned: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    character: Mapped[Character] = relationship(back_populates="inventory")
    item: Mapped[Item | None] = relationship(back_populates="inventory_entries")


class CampaignMap(Base):
    __tablename__ = "maps"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str] = mapped_column(String(500), default="")
    grid_size: Mapped[int | None] = mapped_column(Integer)
    campaign: Mapped[Campaign] = relationship(back_populates="maps")
    markers: Mapped[list["MapMarker"]] = relationship(
        back_populates="map", cascade="all, delete-orphan"
    )
    quest_links: Mapped[list["QuestMap"]] = relationship(
        back_populates="map", cascade="all, delete-orphan"
    )


class MapMarker(Base):
    __tablename__ = "map_markers"
    id: Mapped[int] = mapped_column(primary_key=True)
    map_id: Mapped[int] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    label: Mapped[str] = mapped_column(String(160))
    marker_type: Mapped[str] = mapped_column(String(60), default="Point of interest")
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")
    map: Mapped[CampaignMap] = relationship(back_populates="markers")
    location: Mapped[Location | None] = relationship()


class QuestChapter(Base):
    __tablename__ = "quest_chapters"
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default=QuestChapterStatus.LOCKED)
    summary: Mapped[str] = mapped_column(Text, default="")
    dm_notes: Mapped[str] = mapped_column(Text, default="")
    quest: Mapped[Quest] = relationship(back_populates="chapters")
    objectives: Mapped[list["QuestObjective"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="QuestObjective.sort_order",
    )
    triggers: Mapped[list["QuestTrigger"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )
    rewards: Mapped[list["QuestReward"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )


class QuestObjective(Base):
    __tablename__ = "quest_objectives"
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("quest_chapters.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default=QuestObjectiveStatus.OPEN)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_notes: Mapped[str] = mapped_column(Text, default="")
    quest: Mapped[Quest] = relationship(back_populates="objectives")
    chapter: Mapped[QuestChapter | None] = relationship(back_populates="objectives")


class QuestTrigger(Base):
    __tablename__ = "quest_triggers"
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("quest_chapters.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(160))
    trigger_type: Mapped[str] = mapped_column(String(40), default=QuestTriggerType.MANUAL)
    condition: Mapped[str] = mapped_column(Text, default="")
    effect: Mapped[str] = mapped_column(Text, default="")
    is_fired: Mapped[bool] = mapped_column(Boolean, default=False)
    fired_at: Mapped[datetime | None] = mapped_column(DateTime)
    quest: Mapped[Quest] = relationship(back_populates="triggers")
    chapter: Mapped[QuestChapter | None] = relationship(back_populates="triggers")


class QuestReward(Base):
    __tablename__ = "quest_rewards"
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("quest_chapters.id", ondelete="CASCADE")
    )
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    experience_points: Mapped[int] = mapped_column(Integer, default=0)
    gold_pieces: Mapped[int] = mapped_column(Integer, default=0)
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    quest: Mapped[Quest] = relationship(back_populates="rewards")
    chapter: Mapped[QuestChapter | None] = relationship(back_populates="rewards")
    item: Mapped[Item | None] = relationship(back_populates="rewards")


class QuestMap(Base):
    __tablename__ = "quest_maps"
    __table_args__ = (UniqueConstraint("quest_id", "map_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    map_id: Mapped[int] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(120), default="Reference")
    quest: Mapped[Quest] = relationship(back_populates="map_links")
    map: Mapped[CampaignMap] = relationship(back_populates="quest_links")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("campaign_id", "character_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default=GameStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    campaign: Mapped[Campaign] = relationship(back_populates="games")
    character: Mapped[Character] = relationship(back_populates="games")
    quest: Mapped[Quest | None] = relationship(back_populates="table_games")
    character_links: Mapped[list["GameCharacter"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    session_runs: Mapped[list["SessionRun"]] = relationship(back_populates="game")


class GameCharacter(Base):
    __tablename__ = "game_characters"
    __table_args__ = (UniqueConstraint("game_id", "character_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    game: Mapped[Game] = relationship(back_populates="character_links")
    character: Mapped[Character] = relationship(back_populates="game_links")


class QuestItem(Base):
    __tablename__ = "quest_items"
    __table_args__ = (UniqueConstraint("quest_id", "item_id", "role"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(40), default="Mentioned")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, default="")
    quest: Mapped[Quest] = relationship(back_populates="item_links")
    item: Mapped[Item] = relationship(back_populates="quest_links")


class QuestCharacter(Base):
    __tablename__ = "quest_characters"
    __table_args__ = (UniqueConstraint("quest_id", "character_id", "role"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(80), default="NPC")
    relationship_label: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    quest: Mapped[Quest] = relationship(back_populates="npc_links")
    character: Mapped[Character] = relationship(back_populates="quest_links")


class SessionRun(Base):
    __tablename__ = "session_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id", ondelete="SET NULL"))
    character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL")
    )
    quest_id: Mapped[int | None] = mapped_column(ForeignKey("quests.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160))
    session_number: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default=SessionRunStatus.PLANNED)
    current_scene: Mapped[str] = mapped_column(String(160), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    campaign: Mapped[Campaign] = relationship(back_populates="session_runs")
    game: Mapped[Game | None] = relationship(back_populates="session_runs")
    character: Mapped[Character | None] = relationship(back_populates="session_runs")
    quest: Mapped[Quest | None] = relationship(back_populates="session_runs")
    entries: Mapped[list["SessionEntry"]] = relationship(
        back_populates="session_run",
        cascade="all, delete-orphan",
        order_by="SessionEntry.created_at",
    )


class SessionEntry(Base):
    __tablename__ = "session_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_run_id: Mapped[int] = mapped_column(ForeignKey("session_runs.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(30), default=SessionEntryKind.TABLE_NOTE)
    content: Mapped[str] = mapped_column(Text)
    is_dm_only: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    session_run: Mapped[SessionRun] = relationship(back_populates="entries")


class WorldProfile(Base):
    __tablename__ = "world_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(160))
    premise: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[str] = mapped_column(String(80), default="")
    scope: Mapped[str] = mapped_column(String(100), default="")
    starting_region: Mapped[str] = mapped_column(String(160), default="")
    geography: Mapped[str] = mapped_column(Text, default="")
    everyday_life: Mapped[str] = mapped_column(Text, default="")
    campaign: Mapped[Campaign] = relationship(back_populates="world_profile")
    history_events: Mapped[list["WorldHistoryEvent"]] = relationship(
        back_populates="world", cascade="all, delete-orphan"
    )
    factions: Mapped[list["WorldFaction"]] = relationship(
        back_populates="world", cascade="all, delete-orphan"
    )
    magic_rules: Mapped[list["WorldMagicRule"]] = relationship(
        back_populates="world", cascade="all, delete-orphan"
    )
    starting_situations: Mapped[list["WorldStartingSituation"]] = relationship(
        back_populates="world", cascade="all, delete-orphan"
    )


class WorldHistoryEvent(Base):
    __tablename__ = "world_history_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey("world_profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    public_version: Mapped[str] = mapped_column(Text, default="")
    secret_version: Mapped[str] = mapped_column(Text, default="")
    world: Mapped[WorldProfile] = relationship(back_populates="history_events")


class WorldFaction(Base):
    __tablename__ = "world_factions"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey("world_profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), default="")
    public_purpose: Mapped[str] = mapped_column(Text, default="")
    actual_objective: Mapped[str] = mapped_column(Text, default="")
    internal_tension: Mapped[str] = mapped_column(Text, default="")
    world: Mapped[WorldProfile] = relationship(back_populates="factions")


class WorldMagicRule(Base):
    __tablename__ = "world_magic_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey("world_profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    capability: Mapped[str] = mapped_column(Text, default="")
    cost: Mapped[str] = mapped_column(Text, default="")
    limitation: Mapped[str] = mapped_column(Text, default="")
    world: Mapped[WorldProfile] = relationship(back_populates="magic_rules")


class WorldStartingSituation(Base):
    __tablename__ = "world_starting_situations"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey("world_profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160))
    problem: Mapped[str] = mapped_column(Text, default="")
    visible_stakes: Mapped[str] = mapped_column(Text, default="")
    hidden_stakes: Mapped[str] = mapped_column(Text, default="")
    consequence_of_inaction: Mapped[str] = mapped_column(Text, default="")
    world: Mapped[WorldProfile] = relationship(back_populates="starting_situations")


class WorldDraftChange(Base):
    __tablename__ = "world_draft_changes"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    change_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(160))
    placement: Mapped[str] = mapped_column(String(160), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    consequences: Mapped[str] = mapped_column(Text, default="")
    visibility: Mapped[str] = mapped_column(String(40), default="Draft")
    intended_output: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="Draft")
    source: Mapped[str] = mapped_column(String(30), default="User")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class WorldDraft(Base):
    __tablename__ = "world_drafts"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), unique=True
    )
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    is_reviewing: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
