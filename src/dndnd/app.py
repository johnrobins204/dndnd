import json
import random
import time
from datetime import datetime
from html import escape
from typing import Any, cast

import streamlit as st
from coolname import generate_slug
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from dndnd.config import get_settings
from dndnd.db import create_database_engine, initialize_database, session_scope
from dndnd.llm import OllamaClient, OllamaError
from dndnd.models import (
    Alignment,
    Campaign,
    Character,
    CharacterAbility,
    CharacterAncestry,
    CharacterClass,
    CharacterFeature,
    CharacterJournalEntry,
    CharacterKind,
    CharacterSheet,
    Combatant,
    Encounter,
    InventoryItem,
    Item,
    ItemKind,
    JournalEntry,
    Location,
    Player,
    Quest,
    QuestChapter,
    QuestChapterStatus,
    QuestCharacter,
    QuestItem,
    QuestObjective,
    QuestObjectiveStatus,
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
from dndnd.prompting import (
    WORLD_GUIDANCE_MODES,
    CampaignContext,
    build_session_prompt,
    build_world_guidance_prompt,
)
from dndnd.rules import (
    ANCESTRY_REFERENCES,
    CLASS_REFERENCES,
    COMBAT_RULES_REFERENCE,
    RuleReference,
)
from dndnd.world_checks import check_world_draft
from dndnd.world_export import build_world_brief
from dndnd.world_questions import (
    WORLD_QUESTIONS,
    WorldResponseType,
    WorldStep,
    questions_for_step,
    world_step_order,
)

st.set_page_config(page_title="DNDND", page_icon="🎲", layout="wide")


def render_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #20251f;
            --muted-ink: #697066;
            --parchment: #f7f3e8;
            --paper: #fffdf7;
            --sage: #e4e8d8;
            --brass: #a9782f;
            --ember: #b4472d;
            --line: rgba(32, 37, 31, 0.14);
        }
        .block-container { max-width: 1440px; padding-top: 2rem; }
        [data-testid="stSidebar"] { border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        [data-testid="stSidebar"] [data-testid="stRadio"] {
            width: 100% !important; max-width: none !important;
            flex: 1 1 100% !important; align-self: stretch !important;
        }
        [data-testid="stSidebar"] [data-testid="stElementContainer"]:has(
            [data-testid="stRadio"]
        ) {
            width: 100% !important; max-width: none !important;
            flex: 1 1 100% !important; align-self: stretch !important;
        }
        [data-testid="stSidebar"] [data-testid="stRadioGroup"],
        [data-testid="stSidebar"] [role="radiogroup"] {
            width: 100% !important; max-width: none !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] { gap: .5rem; }
        [data-testid="stSidebar"] [data-testid="stRadioOption"] {
            width: 100% !important; max-width: none !important;
            flex: 1 1 100% !important; box-sizing: border-box;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > div,
        [data-testid="stSidebar"] [role="radiogroup"] > div > label,
        [data-testid="stSidebar"] [role="radiogroup"] > div > label > div,
        [data-testid="stSidebar"] [role="radiogroup"] > label > div,
        [data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] {
            width: 100% !important; max-width: none !important; box-sizing: border-box;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > label {
            display: flex; width: 100%; box-sizing: border-box; padding: .7rem .85rem; margin: 0;
            border: 1px solid var(--line);
            border-radius: 6px; background: rgba(255, 253, 247, .64); cursor: pointer;
            transition: background .15s ease, color .15s ease, border-color .15s ease;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > div > label,
        [data-testid="stSidebar"] [role="radiogroup"] > div > label > div {
            display: flex; padding: .7rem .85rem; margin: 0; border: 1px solid var(--line);
            border-radius: 6px; background: rgba(255, 253, 247, .64); cursor: pointer;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > label:hover {
            border-color: var(--brass); background: var(--paper);
        }
        [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
            border-color: var(--ember); background: var(--ember); color: white;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > div > label:has(input:checked),
        [data-testid="stSidebar"] [role="radiogroup"] > div > label:has(input:checked) > div {
            border-color: var(--ember); background: var(--ember); color: white;
        }
        [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p,
        [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) span {
            color: white;
        }
        [data-testid="stSidebar"] [role="radiogroup"] input { display: none; }
        h1, h2, h3, h4 { letter-spacing: 0; color: var(--ink); }
        p, label, [data-testid="stMarkdownContainer"] { color: var(--ink); }
        .campaign-hero {
            position: relative; overflow: hidden; padding: 2rem 2.2rem 1.8rem;
            margin: 0 0 1.5rem; border: 1px solid var(--line); border-radius: 8px;
            background: linear-gradient(115deg, var(--paper) 0%, var(--sage) 100%);
            box-shadow: 0 12px 30px rgba(32, 37, 31, 0.06);
        }
        .campaign-hero::after {
            content: "✦"; position: absolute; right: 5%; top: 12%; color: var(--brass);
            font-size: 7rem; line-height: 1; opacity: .14; transform: rotate(18deg);
        }
        .campaign-hero .eyebrow, .brief-card .eyebrow {
            color: var(--ember); font-size: .72rem; font-weight: 700; letter-spacing: .12em;
            text-transform: uppercase;
        }
        .campaign-hero h1 { margin: .35rem 0 .5rem; font-size: clamp(2rem, 4vw, 3.4rem); }
        .campaign-hero p {
            max-width: 58rem; margin: 0; color: var(--muted-ink); font-size: 1.05rem;
        }
        .hero-meta { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.2rem; }
        .hero-meta span {
            padding: .35rem .7rem; border: 1px solid var(--line); border-radius: 999px;
            background: rgba(255, 253, 247, .7); color: var(--muted-ink); font-size: .82rem;
        }
        .brief-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .brief-card {
            min-height: 9rem; padding: 1.15rem 1.25rem; border-top: 3px solid var(--brass);
            background: var(--paper); box-shadow: 0 6px 18px rgba(32, 37, 31, .05);
        }
        .brief-card h3 { margin: .45rem 0 .35rem; font-size: 1.2rem; }
        .brief-card p { margin: 0; color: var(--muted-ink); font-size: .92rem; line-height: 1.5; }
        .empty-callout {
            padding: 1rem 1.2rem; border-left: 4px solid var(--ember); background: var(--paper);
            color: var(--muted-ink); font-size: .95rem;
        }
        @media (max-width: 800px) {
            .block-container { padding: 1rem .8rem 2rem; }
            .campaign-hero { padding: 1.35rem; }
            .brief-grid { grid-template-columns: 1fr; }
            .campaign-hero::after { font-size: 4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_campaign_briefing(campaign: Campaign) -> None:
    name = escape(campaign.name)
    summary = escape(
        campaign.summary or "A new campaign waits for its first mark in the chronicle."
    )
    st.markdown(
        f"""
        <section class="campaign-hero">
            <div class="eyebrow">Campaign briefing · D&D 5e (2024)</div>
            <h1>{name}</h1>
            <p>{summary}</p>
            <div class="hero-meta">
                <span>⌖ Local campaign desk</span>
                <span>✦ Player-facing stories</span>
                <span>◈ DM-only state</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def database_engine() -> Engine:
    engine = create_database_engine()
    initialize_database(engine)
    return engine


def campaign_selector(session: Session) -> Campaign | None:
    campaigns = list(session.scalars(select(Campaign).order_by(Campaign.name)))
    if not campaigns:
        st.markdown("## Light the first torch")
        st.write("Create a campaign to open the table, codex, quest board, and chronicle.")
        with st.form("new_campaign", clear_on_submit=True):
            name = st.text_input("Campaign name", placeholder="The Lantern March")
            summary = st.text_area("Premise", placeholder="What is already in motion?")
            if st.form_submit_button("Create campaign", type="primary"):
                if name.strip():
                    session.add(Campaign(name=name.strip(), summary=summary.strip()))
                    session.commit()
                    st.rerun()
                st.error("Campaign name is required.")
        return None

    selector, details = st.columns([2, 3])
    with selector:
        selected = st.selectbox("Campaign", campaigns, format_func=lambda item: item.name)
    with details:
        st.caption("Current campaign")
        st.markdown(f"**{selected.name}** · D&D 5e (2024)")
    with st.expander("Create another campaign"), st.form(
        "new_campaign", clear_on_submit=True
    ):
        name = st.text_input("Campaign name")
        summary = st.text_area("Premise")
        if st.form_submit_button("Create campaign") and name.strip():
            session.add(Campaign(name=name.strip(), summary=summary.strip()))
            session.commit()
            st.rerun()
    return selected


def campaign_rows(session: Session, model: Any, campaign_id: int) -> list[Any]:
    return list(session.scalars(select(model).where(model.campaign_id == campaign_id)))


BACKGROUND_OPTIONS = [
    "Acolyte", "Artisan", "Charlatan", "Criminal", "Entertainer", "Farmer",
    "Guard", "Guide", "Hermit", "Merchant", "Noble", "Pilgrim", "Sage",
    "Sailor", "Scribe", "Soldier", "Wayfarer",
]
SPELLCASTING_ABILITIES = {
    "Bard": "Charisma", "Cleric": "Wisdom", "Druid": "Wisdom", "Ranger": "Wisdom",
    "Sorcerer": "Charisma", "Warlock": "Charisma", "Wizard": "Intelligence",
}
HIT_DICE = {
    "Barbarian": "d12", "Fighter": "d10", "Paladin": "d10", "Ranger": "d10",
    "Bard": "d8", "Cleric": "d8", "Druid": "d8", "Monk": "d8", "Rogue": "d8",
    "Sorcerer": "d6", "Wizard": "d6", "Warlock": "d8",
}
HIT_DIE_SIZES = {class_name: int(hit_die[1:]) for class_name, hit_die in HIT_DICE.items()}
RANDOM_CONCEPTS = [
    "Seeks a lost promise beneath an ordinary life.",
    "Protects a secret that could change the campaign.",
    "Follows an omen no one else can see.",
    "Wants to repay a debt before it comes due.",
    "Is drawn toward danger by an unfinished question.",
]
RANDOM_FEATURES = {
    "Barbarian": "Rage | Enter a focused battle fury",
    "Bard": "Bardic Inspiration | Encourage an ally with a die",
    "Cleric": "Channel Divinity | Call on divine power",
    "Druid": "Wild Shape | Take on a natural form",
    "Fighter": "Second Wind | Recover during a fight",
    "Monk": "Martial Arts | Fight with disciplined technique",
    "Paladin": "Lay on Hands | Restore an ally's vitality",
    "Ranger": "Favored Enemy | Pursue a chosen quarry",
    "Rogue": "Sneak Attack | Exploit an opening",
    "Sorcerer": "Innate Sorcery | Unleash inherent magic",
    "Warlock": "Eldritch Invocation | Shape pact-given power",
    "Wizard": "Spellbook | Prepare a studied repertoire",
}


def proficiency_bonus_for_level(level: int) -> int:
    return 2 + max(0, (level - 1) // 4)


def random_character_draft(players: list[Player]) -> dict[str, Any]:
    class_name = random.choice([item.value for item in CharacterClass])
    ability_names = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    ability_scores = [15, 14, 13, 12, 10, 8]
    random.shuffle(ability_scores)
    ability_values = dict(zip(ability_names, ability_scores, strict=True))
    constitution_modifier = (ability_values["Constitution"] - 10) // 2
    wisdom_modifier = (ability_values["Wisdom"] - 10) // 2
    ancestry = random.choice([item.value for item in CharacterAncestry])
    return {
        "name": "-".join(part.capitalize() for part in generate_slug(2).split("-")),
        "kind": random.choice([item.value for item in CharacterKind]),
        "player_id": random.choice([player.id for player in players]) if players else None,
        "ancestry": ancestry,
        "class_name": class_name,
        "level": 1,
        "background": random.choice(BACKGROUND_OPTIONS),
        "alignment": random.choice([item.value for item in Alignment]),
        "concept": random.choice(RANDOM_CONCEPTS),
        "ability_values": ability_values,
        "ability_method": "Standard array",
        "armor_class": 10 + (ability_values["Dexterity"] - 10) // 2,
        "max_hp": max(1, HIT_DIE_SIZES[class_name] + constitution_modifier),
        "speed": 35 if ancestry == "Goliath" else 30,
        "proficiency_bonus": proficiency_bonus_for_level(1),
        "passive_perception": 10 + wisdom_modifier,
        "hit_dice": HIT_DICE[class_name],
        "spellcasting_ability": SPELLCASTING_ABILITIES.get(class_name, ""),
        "feature_lines": RANDOM_FEATURES[class_name],
        "notes": "Randomized draft. Review the choices before finishing the character.",
    }


ABILITY_NAMES = [
    "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"
]
DICE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
POINT_BUY_BUDGET = 27
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}


def point_buy_total(scores: dict[str, int]) -> int:
    return sum(POINT_BUY_COSTS.get(score, 999) for score in scores.values())


def generate_ability_scores(method: str) -> dict[str, int]:
    if method == "Standard array":
        scores = [15, 14, 13, 12, 10, 8]
        random.shuffle(scores)
    else:
        scores = []
        for _ in ABILITY_NAMES:
            rolls = sorted(random.randint(1, 6) for _ in range(4))
            scores.append(sum(rolls[1:]))
    return dict(zip(ABILITY_NAMES, scores, strict=True))


def build_roll_board(
    method: str,
    landed_scores: dict[str, int],
    active_name: str | None = None,
    active_frame: int = 0,
    active_phase: str = "rolling",
) -> list[str]:
    board = [f"### Ability score roll · {method}", ""]
    for ability_index, ability_name in enumerate(ABILITY_NAMES):
        if ability_name in landed_scores:
            board.append(f"✅ **{ability_name}** · **{landed_scores[ability_name]}**")
        elif ability_name == active_name:
            face = DICE_FACES[(ability_index + active_frame) % len(DICE_FACES)]
            board.append(f"{face} **{ability_name}** · {active_phase}...")
        else:
            board.append(f"○ **{ability_name}** · waiting")
    return board


def render_roll_board(
    animation: Any,
    method: str,
    landed_scores: dict[str, int],
    active_name: str | None = None,
    active_frame: int = 0,
    active_phase: str = "rolling",
) -> None:
    animation.markdown(
        "\n\n".join(
            build_roll_board(method, landed_scores, active_name, active_frame, active_phase)
        )
    )


def animate_ability_scores(method: str) -> dict[str, int]:
    scores = generate_ability_scores(method)
    animation = st.empty()
    progress = st.progress(0, text="The dice are in motion...")
    landed_scores: dict[str, int] = {}
    for ability_index, ability_name in enumerate(ABILITY_NAMES):
        for frame_index in range(6):
            render_roll_board(
                animation, method, landed_scores, ability_name, frame_index, "rolling"
            )
            time.sleep(0.08)
        render_roll_board(animation, method, landed_scores, ability_name, 5, "lands")
        time.sleep(0.12)
        landed_scores[ability_name] = scores[ability_name]
        render_roll_board(animation, method, landed_scores)
        progress.progress(
            (ability_index + 1) / len(ABILITY_NAMES),
            text=f"{ability_name} locked in",
        )
        time.sleep(0.1)
    render_roll_board(animation, method, landed_scores)
    return scores


def workspace_navigation() -> str:
    st.sidebar.markdown("### Workspace")
    return st.sidebar.radio(
        "Workspace",
        ["Briefing", "The Table", "Party", "World", "Journal", "Quests", "Combat", "Writer"],
        key="workspace_view",
        label_visibility="collapsed",
    )


def table_page(session: Session, campaign: Campaign) -> None:
    st.subheader("The Table")
    st.caption("Run the session, keep the fiction moving, and capture canon as it happens.")
    runs = list(
        session.scalars(
            select(SessionRun)
            .where(SessionRun.campaign_id == campaign.id)
            .order_by(SessionRun.created_at.desc())
        )
    )
    with st.expander("Prepare a new session", expanded=not runs), st.form(
        "new_session_run", clear_on_submit=True
    ):
        title = st.text_input("Session title", placeholder="The lighthouse below the tide")
        session_number = st.number_input("Session number", 0, 9999, 0)
        summary = st.text_area("Preparation notes")
        if st.form_submit_button("Create session", type="primary") and title.strip():
            session.add(
                SessionRun(
                    campaign_id=campaign.id,
                    title=title.strip(),
                    session_number=session_number or None,
                    summary=summary,
                )
            )
            session.commit()
            st.rerun()
    if not runs:
        st.info("Create a session to open the table view.")
        return

    current = st.selectbox(
        "Session", runs, format_func=lambda item: f"{item.title} · {item.status}"
    )
    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.markdown(f"### {current.title}")
        st.caption(
            f"{current.status} · Scene: {current.current_scene or 'Not set'} · "
            f"{len(current.entries)} transcript entries"
        )
    with header_right:
        if current.status != SessionRunStatus.ACTIVE and st.button(
            "Begin session", key=f"begin_session_{current.id}", type="primary"
        ):
            current.status = SessionRunStatus.ACTIVE
            current.started_at = datetime.now()
            current.entries.append(
                SessionEntry(kind=SessionEntryKind.SYSTEM, content="Session began.")
            )
            session.commit()
            st.rerun()
        if current.status == SessionRunStatus.ACTIVE and st.button(
            "Close session", key=f"close_session_{current.id}"
        ):
            current.status = SessionRunStatus.COMPLETE
            current.ended_at = datetime.now()
            current.entries.append(
                SessionEntry(kind=SessionEntryKind.SYSTEM, content="Session closed.")
            )
            session.commit()
            st.rerun()

    transcript, context = st.columns([2, 1])
    with transcript:
        with st.form(f"table_command_{current.id}", clear_on_submit=True):
            command = st.text_input(
                "Table input",
                placeholder=(
                    "/scene The drowned archive  ·  /say The bell rings below  ·  "
                    "/note Ask about the sigil"
                ),
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Capture", type="primary", use_container_width=True)
        if submitted and command.strip():
            raw = command.strip()
            lowered = raw.casefold()
            if lowered.startswith("/scene "):
                scene = raw[7:].strip()
                current.current_scene = scene
                entry = SessionEntry(kind=SessionEntryKind.SCENE, content=scene)
            elif lowered.startswith("/say "):
                entry = SessionEntry(kind=SessionEntryKind.NARRATION, content=raw[5:].strip())
            elif lowered.startswith("/note "):
                entry = SessionEntry(
                    kind=SessionEntryKind.DM_NOTE, content=raw[6:].strip(), is_dm_only=True
                )
            else:
                entry = SessionEntry(kind=SessionEntryKind.TABLE_NOTE, content=raw)
            current.entries.append(entry)
            if current.status == SessionRunStatus.PLANNED:
                current.status = SessionRunStatus.ACTIVE
                current.started_at = datetime.now()
            session.commit()
            st.rerun()
        st.markdown("#### Transcript")
        if not current.entries:
            st.info("The table is quiet. Begin with a scene, narration, or DM note above.")
        for entry in current.entries:
            if entry.kind == SessionEntryKind.SCENE:
                st.markdown(f"##### Scene · {entry.content}")
            elif entry.is_dm_only:
                st.warning(f"DM note · {entry.content}")
            elif entry.kind == SessionEntryKind.NARRATION:
                st.markdown(f"> {entry.content}")
            elif entry.kind == SessionEntryKind.SYSTEM:
                st.caption(entry.content)
            else:
                st.markdown(f"**Table note** · {entry.content}")
            st.caption(f"{entry.created_at:%H:%M}")
    with context:
        st.markdown("#### At a glance")
        active_quests = list(
            session.scalars(
                select(Quest)
                .where(Quest.campaign_id == campaign.id, Quest.status == QuestStatus.ACTIVE)
                .order_by(Quest.title)
                .limit(5)
            )
        )
        st.markdown("**Active threads**")
        for quest in active_quests:
            st.markdown(f"- {quest.title}")
        characters = campaign_rows(session, Character, campaign.id)
        st.markdown("**Present cast**")
        for character in characters[:8]:
            st.markdown(f"- {character.name} · {character.current_hp}/{character.max_hp} HP")
        with st.form(f"scene_state_{current.id}"):
            scene = st.text_input("Current scene", value=current.current_scene)
            if st.form_submit_button("Update scene") and scene.strip():
                current.current_scene = scene.strip()
                current.entries.append(
                    SessionEntry(kind=SessionEntryKind.SCENE, content=scene.strip())
                )
                session.commit()
                st.rerun()


def dashboard(session: Session, campaign: Campaign) -> None:
    render_campaign_briefing(campaign)
    columns = st.columns(4)
    for column, model, label in zip(
        columns,
        [Character, Location, Quest, JournalEntry],
        ["Characters", "Locations", "Quests", "Journal entries"],
        strict=True,
    ):
        column.metric(label, len(campaign_rows(session, model, campaign.id)))
    active_quests = list(
        session.scalars(
            select(Quest)
            .where(Quest.campaign_id == campaign.id, Quest.status == QuestStatus.ACTIVE)
            .order_by(Quest.title)
        )
    )
    recent_entries = list(
        session.scalars(
            select(JournalEntry)
            .where(JournalEntry.campaign_id == campaign.id)
            .order_by(JournalEntry.occurred_at.desc())
            .limit(3)
        )
    )
    left, right = st.columns(2)
    with left:
        st.markdown("#### Active threads")
        if active_quests:
            for quest in active_quests:
                st.markdown(f"**{quest.title}**  \n{quest.objective or 'Objective not recorded.'}")
        else:
            st.info("No active quests yet. Add the first thread from the Quests tab.")
    with right:
        st.markdown("#### Last table notes")
        if recent_entries:
            for entry in recent_entries:
                st.markdown(f"**{entry.title}** · {entry.occurred_at:%b %d}  \n{entry.body[:180]}")
        else:
            st.info("Your table history will appear here after the first journal entry.")
    st.markdown(
        """
        <div class="brief-grid">
            <article class="brief-card">
                <div class="eyebrow">Cartography</div>
                <h3>Places worth returning to</h3>
                <p>Keep locations, maps, thresholds, and secrets close to the story they serve.</p>
            </article>
            <article class="brief-card">
                <div class="eyebrow">The cast</div>
                <h3>People with unfinished business</h3>
                <p>Characters and NPCs should feel connected to motives, memories, and
                consequences.</p>
            </article>
            <article class="brief-card">
                <div class="eyebrow">The next move</div>
                <h3>Prepare the table</h3>
                <p>Open The Table to frame a scene, capture a note, or begin tonight's session.</p>
            </article>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alignment_grid(current: str, widget_key: str) -> str:
    st.markdown("**Alignment**")
    st.caption("Optional. Choose a cell or leave alignment unset.")
    rows = [
        [Alignment.LAWFUL_GOOD, Alignment.NEUTRAL_GOOD, Alignment.CHAOTIC_GOOD],
        [Alignment.LAWFUL_NEUTRAL, Alignment.TRUE_NEUTRAL, Alignment.CHAOTIC_NEUTRAL],
        [Alignment.LAWFUL_EVIL, Alignment.NEUTRAL_EVIL, Alignment.CHAOTIC_EVIL],
    ]
    selected = cast(str, st.session_state.get(widget_key, current))
    for row_index, row in enumerate(rows):
        columns = st.columns(3)
        for column, alignment in zip(columns, row, strict=True):
            if column.button(
                alignment.value,
                key=f"{widget_key}_{row_index}_{alignment.value}",
                type="primary" if selected == alignment.value else "secondary",
                use_container_width=True,
            ):
                st.session_state[widget_key] = alignment.value
                st.rerun()
    st.caption(f"Selected: {selected or 'Not set'}")
    return selected


def render_rule_reference(reference: RuleReference, key: str) -> None:
    official_link = (
        f"<a href='{escape(reference.official_url)}' target='_blank' rel='noreferrer'>"
        "Official 2024 rules ↗</a> · "
        if reference.official_url else ""
    )
    st.markdown(
        f"<div class='empty-callout' key='{escape(key)}'>"
        f"<strong>{escape(reference.name)}</strong><br>{escape(reference.summary)}<br>"
        f"{official_link}"
        f"<a href='{escape(reference.wiki_url)}' target='_blank' rel='noreferrer'>"
        "Read the reference wiki ↗</a></div>",
        unsafe_allow_html=True,
    )


def character_workspace(session: Session, campaign: Campaign, character: Character) -> None:
    st.markdown(f"### {character.name}")
    st.caption(
        f"{character.ancestry or 'Ancestry unset'} · {character.class_name or 'Role unset'} · "
        f"Level {character.level} · {character.current_hp}/{character.max_hp} HP"
    )
    sheet_tab, journal_tab, inventory_tab, features_tab = st.tabs(
        ["Sheet", "Character journal", "Inventory", "Features"]
    )
    with sheet_tab:
        render_character_sheet(character)
        sheet = character.sheet
        alignment = alignment_grid(
            sheet.alignment if sheet else "", f"alignment_sheet_{character.id}"
        )
        with st.form(f"sheet_{character.id}"):
            left, middle, right = st.columns(3)
            background = left.text_input("Background", value=sheet.background if sheet else "")
            experience = left.number_input(
                "Experience points", 0, 999999, sheet.experience_points if sheet else 0
            )
            temporary_hp = middle.number_input(
                "Temporary HP", 0, 999, sheet.temporary_hp if sheet else 0
            )
            hit_dice = middle.text_input("Hit dice", value=sheet.hit_dice if sheet else "")
            speed = middle.number_input("Speed", 0, 200, sheet.speed if sheet else 30)
            right.metric("Proficiency bonus", sheet.proficiency_bonus if sheet else 2)
            right.metric("Passive perception", sheet.passive_perception if sheet else 10)
            inspiration = right.checkbox("Inspiration", value=sheet.inspiration if sheet else False)
            spellcasting = st.text_input(
                "Spellcasting ability", value=sheet.spellcasting_ability if sheet else ""
            )
            notes = st.text_area("Sheet notes", value=sheet.notes if sheet else "")
            if st.form_submit_button("Save sheet", type="primary"):
                if sheet is None:
                    sheet = CharacterSheet(character=character)
                    session.add(sheet)
                sheet.background = background
                sheet.alignment = alignment
                sheet.experience_points = experience
                sheet.temporary_hp = temporary_hp
                sheet.hit_dice = hit_dice
                sheet.speed = speed
                sheet.inspiration = inspiration
                sheet.spellcasting_ability = spellcasting
                sheet.notes = notes
                session.commit()
                st.rerun()
    with journal_tab:
        with st.form(f"character_journal_{character.id}", clear_on_submit=True):
            title = st.text_input("Entry title")
            kind = st.selectbox("Entry type", ["Memory", "Secret", "Relationship", "Goal", "Note"])
            body = st.text_area("Entry", height=140)
            session_number = st.number_input("Session", 0, 9999, 0)
            private = st.checkbox("DM-only", value=True)
            tags = st.text_input("Tags")
            if st.form_submit_button("Add character entry") and title.strip() and body.strip():
                session.add(
                    CharacterJournalEntry(
                        character=character, title=title.strip(), kind=kind, body=body.strip(),
                        session_number=session_number or None, is_private=private, tags=tags,
                    )
                )
                session.commit()
                st.rerun()
        for entry in sorted(
            character.journal_entries, key=lambda item: item.created_at, reverse=True
        ):
            label = "DM-only" if entry.is_private else "table-visible"
            with st.expander(f"{entry.title} · {entry.kind} · {label}"):
                st.caption(
                    f"Session {entry.session_number or 'unspecified'} · "
                    f"{entry.tags or 'untagged'}"
                )
                st.write(entry.body)
    with inventory_tab:
        items = campaign_rows(session, Item, campaign.id)
        with st.expander("Create campaign item"), st.form(
            f"new_item_{character.id}", clear_on_submit=True
        ):
            item_name = st.text_input("Item name")
            item_kind = st.selectbox("Item type", [item.value for item in ItemKind])
            description = st.text_area("Description")
            rarity = st.text_input("Rarity")
            if st.form_submit_button("Create item") and item_name.strip():
                session.add(
                    Item(
                        campaign_id=campaign.id, name=item_name.strip(), kind=item_kind,
                        description=description, rarity=rarity,
                    )
                )
                session.commit()
                st.rerun()
        if items:
            with st.form(f"inventory_{character.id}", clear_on_submit=True):
                item = st.selectbox("Item", items, format_func=lambda value: value.name)
                quantity = st.number_input("Quantity", 1, 999, 1)
                equipped = st.checkbox("Equipped")
                attuned = st.checkbox("Attuned")
                notes = st.text_input("Inventory notes")
                if st.form_submit_button("Add to inventory"):
                    session.add(
                        InventoryItem(
                            character=character, item=item, quantity=quantity,
                            equipped=equipped, attuned=attuned, notes=notes,
                        )
                    )
                    session.commit()
                    st.rerun()
        else:
            st.info("Create a campaign item before adding inventory.")
        st.dataframe(
            [
                {
                    "Item": entry.custom_name
                    or (entry.item.name if entry.item else "Unlinked item"),
                    "Qty": entry.quantity,
                    "Equipped": entry.equipped,
                    "Attuned": entry.attuned,
                    "Notes": entry.notes,
                }
                for entry in character.inventory
            ],
            use_container_width=True,
            hide_index=True,
        )
    with features_tab:
        with st.form(f"feature_{character.id}", clear_on_submit=True):
            name = st.text_input("Feature name")
            category = st.text_input("Category", value="Feature")
            source = st.text_input("Source")
            description = st.text_area("Rules text / DM reminder")
            uses_max = st.number_input("Uses", 0, 99, 0)
            if st.form_submit_button("Add feature") and name.strip():
                session.add(
                    CharacterFeature(
                        character=character, name=name.strip(), category=category,
                        source=source, description=description,
                        uses_max=uses_max or None, uses_remaining=uses_max or None,
                    )
                )
                session.commit()
                st.rerun()
        for feature in character.features:
            st.markdown(f"**{feature.name}** · {feature.category}")
            st.caption(feature.source or "No source recorded")
            st.write(feature.description or "No description recorded.")


def new_character_interview(session: Session, campaign: Campaign, players: list[Player]) -> None:
    draft_key = f"character_draft_{campaign.id}"
    step_key = f"character_step_{campaign.id}"
    draft: dict[str, Any] = st.session_state.setdefault(draft_key, {})
    step = st.session_state.get(step_key, 1)
    st.markdown("### New Character")
    st.caption("A guided pass from character concept to engine-ready sheet data.")
    st.progress((step - 1) / 4, text=f"Step {step} of 4")

    if step == 1:
        st.markdown("#### 1 · Identity and concept")
        st.write("Start with the character the player wants to bring to the table.")
        if st.button("🎲 Roll random character", key=f"random_character_{campaign.id}"):
            draft.clear()
            draft.update(random_character_draft(players))
            draft["ability_method"] = "Dice roll (4d6, drop lowest)"
            draft["ability_values"] = animate_ability_scores(draft["ability_method"])
            st.session_state[f"alignment_interview_{campaign.id}"] = draft["alignment"]
            st.session_state[f"interview_ancestry_{campaign.id}"] = draft["ancestry"]
            st.session_state[f"interview_class_{campaign.id}"] = draft["class_name"]
            st.rerun()
        alignment = alignment_grid(
            draft.get("alignment", ""), f"alignment_interview_{campaign.id}"
        )
        ancestry_options = [item.value for item in CharacterAncestry]
        class_options = [item.value for item in CharacterClass]
        ancestry = st.selectbox(
            "Species / ancestry",
            ancestry_options,
            index=(
                ancestry_options.index(draft["ancestry"])
                if draft.get("ancestry") in ancestry_options else 0
            ),
            key=f"interview_ancestry_{campaign.id}",
        )
        render_rule_reference(ANCESTRY_REFERENCES[ancestry], "ancestry_reference")
        class_name = st.selectbox(
            "Class",
            class_options,
            index=(
                class_options.index(draft["class_name"])
                if draft.get("class_name") in class_options else 0
            ),
            key=f"interview_class_{campaign.id}",
        )
        render_rule_reference(CLASS_REFERENCES[class_name], "class_reference")
        with st.form("character_interview_identity"):
            left, right = st.columns(2)
            name = left.text_input("Character name", value=draft.get("name", ""))
            kind = left.selectbox("Character type", [item.value for item in CharacterKind])
            player_id = left.selectbox(
                "Player", [None, *[player.id for player in players]],
                format_func=lambda value: (
                    "Unassigned" if value is None
                    else next(player.name for player in players if player.id == value)
                ),
            )
            level = right.number_input("Starting level", 1, 20, draft.get("level", 1))
            background = st.text_input("Background", value=draft.get("background", ""))
            concept = st.text_area(
                "Concept and motivations", value=draft.get("concept", ""),
                placeholder="What does this character want, fear, or protect?",
            )
            if st.form_submit_button("Continue to ability scores", type="primary"):
                if not name.strip() or not ancestry.strip() or not class_name.strip():
                    st.error("Name, ancestry, and class or role are required.")
                else:
                    draft.update(
                        name=name.strip(), kind=kind, player_id=player_id,
                        ancestry=ancestry.strip(), class_name=class_name.strip(),
                        level=level, background=background.strip(),
                        alignment=alignment.strip(), concept=concept.strip(),
                    )
                    st.session_state[step_key] = 2
                    st.rerun()
    elif step == 2:
        st.markdown("#### 2 · Ability scores")
        st.write(
            "Enter the final assigned scores. The engine will derive modifiers and save bonuses."
        )
        methods = [
            "Dice roll (4d6, drop lowest)", "Standard array",
            "Point buy final scores", "Manual entry",
        ]
        method = st.selectbox(
            "Generation method", methods,
            index=methods.index(draft.get("ability_method", methods[0])),
            key=f"interview_ability_method_{campaign.id}",
        )
        st.caption("Scores stay hidden while the dice roll, then land one at a time.")
        if st.button("🎲 Roll ability scores", key=f"roll_abilities_{campaign.id}"):
            draft["ability_values"] = animate_ability_scores(method)
            draft["ability_method"] = method
            for ability_name, score in draft["ability_values"].items():
                st.session_state[f"interview_{ability_name}"] = score
            st.rerun()
        with st.form("character_interview_abilities"):
            defaults = [15, 14, 13, 12, 10, 8]
            stored_scores = draft.get("ability_values", {})
            minimum_score = 8 if method == "Point buy final scores" else 1
            maximum_score = 15 if method == "Point buy final scores" else 20
            ability_values = {
                ability_name: st.number_input(
                    ability_name, minimum_score, maximum_score,
                    min(
                        maximum_score,
                        max(minimum_score, stored_scores.get(ability_name, defaults[index])),
                    ),
                    key=f"interview_{ability_name}",
                )
                for index, ability_name in enumerate(ABILITY_NAMES)
            }
            if method == "Point buy final scores":
                spent_points = point_buy_total(ability_values)
                st.caption(
                    f"Point buy: {spent_points}/{POINT_BUY_BUDGET} points spent. "
                    "Scores must use the full 27-point budget."
                )
            else:
                st.caption(f"Method recorded for provenance: {method}.")
            back, forward = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 1
                st.rerun()
            if forward.form_submit_button("Continue to combat details", type="primary"):
                if (
                    method == "Point buy final scores"
                    and point_buy_total(ability_values) != POINT_BUY_BUDGET
                ):
                    st.error("Point buy must spend exactly 27 points before continuing.")
                else:
                    draft.update(ability_values=ability_values, ability_method=method)
                    st.session_state[step_key] = 3
                    st.rerun()
    elif step == 3:
        st.markdown("#### 3 · Combat and rules state")
        st.write("These values become the compact combat-facing part of the character sheet.")
        render_rule_reference(COMBAT_RULES_REFERENCE, "combat_rules_reference")
        ability_values = draft.get("ability_values", {})
        dexterity_modifier = (ability_values.get("Dexterity", 10) - 10) // 2
        constitution_modifier = (ability_values.get("Constitution", 10) - 10) // 2
        level = draft.get("level", 1)
        class_name = draft.get("class_name", "Fighter")
        derived_base_ac = 10 + dexterity_modifier
        derived_max_hp = max(1, HIT_DIE_SIZES[class_name] + constitution_modifier)
        derived_proficiency = proficiency_bonus_for_level(level)
        derived_passive_perception = 10 + (ability_values.get("Wisdom", 10) - 10) // 2
        derived_hit_die = HIT_DICE[class_name]
        derived_spellcasting = SPELLCASTING_ABILITIES.get(class_name, "")
        with st.form("character_interview_combat"):
            left, middle, right = st.columns(3)
            armor_class = left.number_input(
                "Armor class (current)", 0, 40,
                draft.get("armor_class", derived_base_ac),
            )
            left.caption(
                "Base calculation: 10 + Dexterity modifier; armor and features can change it."
            )
            left.metric("Maximum hit points", derived_max_hp)
            left.caption(f"Level 1 default: {derived_hit_die} maximum + Constitution modifier.")
            max_hp = derived_max_hp
            speed = middle.number_input("Speed (feet)", 0, 200, draft.get("speed", 30))
            middle.metric("Proficiency bonus", derived_proficiency)
            middle.caption("Derived from level; +2 at levels 1–4.")
            right.metric("Passive perception (base)", derived_passive_perception)
            passive_perception = derived_passive_perception
            right.metric("Hit die", derived_hit_die)
            right.metric("Spellcasting ability", derived_spellcasting or "None")
            proficiency = derived_proficiency
            hit_dice = derived_hit_die
            spellcasting = derived_spellcasting
            back, forward = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 2
                st.rerun()
            if forward.form_submit_button("Continue to story and features", type="primary"):
                draft.update(
                    armor_class=armor_class, max_hp=max_hp, speed=speed,
                    proficiency_bonus=proficiency, passive_perception=passive_perception,
                    hit_dice=hit_dice.strip(), spellcasting_ability=spellcasting.strip(),
                )
                st.session_state[step_key] = 4
                st.rerun()
    else:
        st.markdown("#### 4 · Story and features")
        st.write("Finish with the information that makes the sheet playable at the table.")
        with st.form("character_interview_story"):
            notes = st.text_area("Character notes", value=draft.get("notes", ""))
            feature_lines = st.text_area(
                "Features and proficiencies",
                value=draft.get("feature_lines", ""),
                placeholder=(
                    "Second Wind | Recover during a fight\n"
                    "Arcane Recovery | Restore magical resources"
                ),
            )
            back, finish = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 3
                st.rerun()
            if finish.form_submit_button("Finish character", type="primary"):
                character = Character(
                    campaign_id=campaign.id, player_id=draft.get("player_id"),
                    name=draft["name"], kind=draft["kind"], ancestry=draft["ancestry"],
                    class_name=draft["class_name"], level=draft["level"],
                    armor_class=draft["armor_class"], max_hp=draft["max_hp"],
                    current_hp=draft["max_hp"], notes=notes.strip(),
                )
                character.sheet = CharacterSheet(
                    background=draft["background"], alignment=draft["alignment"],
                    speed=draft["speed"], proficiency_bonus=draft["proficiency_bonus"],
                    passive_perception=draft["passive_perception"], hit_dice=draft["hit_dice"],
                    spellcasting_ability=draft["spellcasting_ability"], notes=draft["concept"],
                )
                for ability_name, score in draft["ability_values"].items():
                    modifier = (score - 10) // 2
                    character.abilities.append(
                        CharacterAbility(
                            ability_name=ability_name, score=score, modifier=modifier,
                            save_bonus=modifier,
                        )
                    )
                for feature_line in feature_lines.splitlines():
                    if feature_line.strip():
                        feature_name, _, description = feature_line.partition("|")
                        character.features.append(
                            CharacterFeature(
                                name=feature_name.strip(), description=description.strip()
                            )
                        )
                session.add(character)
                session.commit()
                st.session_state.pop(draft_key, None)
                st.session_state.pop(step_key, None)
                st.success(f"{character.name} is ready for the table.")
                st.rerun()


def render_character_sheet(character: Character) -> None:
    st.markdown("#### Character sheet")
    identity = st.columns(4)
    identity[0].metric("Class / role", character.class_name or "Unset")
    identity[1].metric("Level", character.level)
    identity[2].metric("Armor class", character.armor_class)
    identity[3].metric("Hit points", f"{character.current_hp}/{character.max_hp}")
    st.markdown("##### Ability scores")
    ability_columns = st.columns(6)
    abilities = {ability.ability_name: ability for ability in character.abilities}
    for column, ability_name in zip(
        ability_columns,
        ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
        strict=True,
    ):
        ability = abilities.get(ability_name)
        column.metric(ability_name[:3].upper(), ability.score if ability else "—",
                      f"{ability.modifier:+d}" if ability else "")
    sheet = character.sheet
    rules = st.columns(5)
    rules[0].metric("Speed", sheet.speed if sheet else "—")
    rules[1].metric("Prof.", sheet.proficiency_bonus if sheet else "—")
    rules[2].metric("Passive", sheet.passive_perception if sheet else "—")
    rules[3].metric("Hit dice", sheet.hit_dice if sheet else "—")
    rules[4].metric("Spellcasting", sheet.spellcasting_ability or "—" if sheet else "—")
    if character.features:
        st.markdown("##### Features and proficiencies")
        st.dataframe(
            [{"Feature": feature.name, "Category": feature.category,
              "Reminder": feature.description} for feature in character.features],
            use_container_width=True, hide_index=True,
        )


def party_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Party & cast")
    players = campaign_rows(session, Player, campaign.id)
    with st.expander("Add player"), st.form("add_player", clear_on_submit=True):
        name = st.text_input("Player name")
        notes = st.text_area("Notes")
        if st.form_submit_button("Add player") and name.strip():
            session.add(Player(campaign_id=campaign.id, name=name.strip(), notes=notes))
            session.commit()
            st.rerun()
    characters = campaign_rows(session, Character, campaign.id)
    with st.expander("New Character", expanded=not characters):
        new_character_interview(session, campaign, players)
    st.dataframe(
        [
            {
                "Name": item.name,
                "Type": item.kind,
                "Player": item.player.name if item.player else "",
                "Species": item.ancestry,
                "Class / role": item.class_name,
                "Level": item.level,
                "AC": item.armor_class,
                "HP": f"{item.current_hp}/{item.max_hp}",
            }
            for item in campaign_rows(session, Character, campaign.id)
        ],
        use_container_width=True,
        hide_index=True,
    )
    if characters:
        selected_id = st.selectbox(
            "Open character workspace",
            [character.id for character in characters],
            format_func=lambda character_id: next(
                f"{character.name} · {character.kind}"
                for character in characters
                if character.id == character_id
            ),
            key=f"selected_character_{campaign.id}",
        )
        selected = session.get(Character, selected_id)
        if selected is not None:
            character_workspace(session, campaign, selected)


def world_page(session: Session, campaign: Campaign) -> None:
    st.subheader("World")
    with st.expander("Build or expand the world", expanded=True):
        world_builder(session, campaign)
    with st.expander("Add to existing world"):
        world_add_flow(session, campaign)
    st.divider()
    st.markdown("#### Locations")
    with st.form("add_location", clear_on_submit=True):
        name = st.text_input("Location")
        environment = st.text_input("Environment", placeholder="Urban, forest, dungeon…")
        description = st.text_area("What players can observe")
        secrets = st.text_area("DM-only secrets")
        if st.form_submit_button("Add location", type="primary") and name.strip():
            session.add(
                Location(
                    campaign_id=campaign.id,
                    name=name.strip(),
                    environment=environment,
                    description=description,
                    secrets=secrets,
                )
            )
            session.commit()
            st.rerun()
    for location in campaign_rows(session, Location, campaign.id):
        with st.expander(f"{location.name} · {location.environment or 'Unclassified'}"):
            st.write(location.description or "No public description yet.")
            if location.secrets:
                st.warning(f"DM secret: {location.secrets}")


def world_add_flow(session: Session, campaign: Campaign) -> None:
    st.markdown("#### Add to the world")
    st.caption("Create a reviewable contribution without changing canon immediately.")
    with st.form(f"world_add_{campaign.id}", clear_on_submit=True):
        change_type = st.selectbox(
            "What are you adding?",
            [
                "Location", "Faction", "Historical event", "Culture", "Religion",
                "Magic rule", "NPC group", "Conflict", "Adventure hook",
            ],
        )
        title = st.text_input("Name or short title")
        placement = st.text_input(
            "Where does it belong?",
            placeholder="Existing region, settlement, faction, timeline, or new branch",
        )
        details = st.text_area("What is it?")
        consequences = st.text_area("What does it change? Who benefits or is threatened?")
        visibility = st.selectbox(
            "How visible is it?",
            ["Public fact", "Local knowledge", "Secret", "Rumor", "False belief"],
        )
        intended_output = st.selectbox(
            "What should the DM get from it?",
            ["NPC seed", "Quest hook", "Location detail", "Conflict", "Encounter idea",
             "Player-facing description"],
        )
        if st.form_submit_button("Save as draft change", type="primary"):
            if not title.strip() or not details.strip():
                st.error("Add a title and details before saving the draft.")
            else:
                session.add(
                    WorldDraftChange(
                        campaign_id=campaign.id, change_type=change_type, title=title.strip(),
                        placement=placement.strip(), details=details.strip(),
                        consequences=consequences.strip(), visibility=visibility,
                        intended_output=intended_output,
                    )
                )
                session.commit()
                st.rerun()
    drafts = list(
        session.scalars(
            select(WorldDraftChange)
            .where(WorldDraftChange.campaign_id == campaign.id)
            .order_by(WorldDraftChange.created_at.desc())
        )
    )
    if drafts:
        st.markdown("#### Pending world changes")
        for change in drafts:
            with st.expander(f"{change.title} · {change.change_type} · {change.status}"):
                st.caption(f"{change.visibility} · {change.intended_output}")
                st.write(change.details)
                if change.placement:
                    st.write(f"**Placement:** {change.placement}")
                if change.consequences:
                    st.write(f"**Consequences:** {change.consequences}")


def world_builder(session: Session, campaign: Campaign) -> None:
    draft_key = f"world_draft_{campaign.id}"
    step_key = f"world_step_{campaign.id}"
    persisted_draft = session.scalar(
        select(WorldDraft).where(WorldDraft.campaign_id == campaign.id)
    )
    if draft_key not in st.session_state:
        st.session_state[draft_key] = (
            json.loads(persisted_draft.answers_json) if persisted_draft else {}
        )
    if step_key not in st.session_state and persisted_draft:
        st.session_state[step_key] = persisted_draft.current_step
    if persisted_draft and persisted_draft.is_reviewing:
        st.session_state[f"world_review_{campaign.id}"] = True
    persisted_answers = json.loads(persisted_draft.answers_json) if persisted_draft else {}
    if persisted_answers.get("_review_opened"):
        st.session_state[f"world_review_opened_{campaign.id}"] = True
    draft: dict[str, str] = st.session_state[draft_key]
    steps = world_step_order()
    step_index = int(st.session_state.get(step_key, 0))
    step_index = max(0, min(step_index, len(steps) - 1))
    current_step = steps[step_index]
    step_questions = questions_for_step(current_step)

    st.markdown("### World builder")
    st.caption("A focused path from premise to a playable starting situation.")
    st.progress(
        (step_index + 1) / len(steps),
        text=f"Step {step_index + 1} of {len(steps)} · {current_step.replace('_', ' ').title()}",
    )

    summary, questions = st.columns([1, 2])
    with summary:
        st.markdown("#### World taking shape")
        completed = 0
        for question in WORLD_QUESTIONS:
            value = draft.get(question.key, "")
            if value and value != question.uncertainty_option:
                completed += 1
        st.metric("Answered", f"{completed}/{len(WORLD_QUESTIONS)}")
        for key, label in (
            ("world_name", "Name"),
            ("premise", "Premise"),
            ("scope", "Scope"),
            ("starting_region", "Starting region"),
            ("starting_problem", "Current problem"),
        ):
            summary_value = draft.get(key)
            if summary_value:
                st.markdown(f"**{label}**  \n{summary_value[:120]}")
            else:
                st.caption(f"{label} · not set")
    with questions:
        st.markdown(f"#### {current_step.replace('_', ' ').title()}")
        st.write("Answer what you know. You can leave uncertainty visible and return later.")
        with st.form(f"world_step_{campaign.id}_{current_step}"):
            responses: dict[str, str] = {}
            for question in step_questions:
                st.markdown(f"**{question.prompt}**")
                if question.help_text:
                    st.caption(question.help_text)
                options = (question.uncertainty_option, *question.options)
                if question.response_type is WorldResponseType.SINGLE_CHOICE:
                    existing = draft.get(question.key, question.uncertainty_option)
                    responses[question.key] = st.selectbox(
                        question.key,
                        options,
                        index=options.index(existing) if existing in options else 0,
                        label_visibility="collapsed",
                    ) or ""
                elif question.response_type is WorldResponseType.LONG_TEXT:
                    responses[question.key] = st.text_area(
                        question.key,
                        value=draft.get(question.key, ""),
                        height=120,
                        placeholder=question.uncertainty_option,
                        label_visibility="collapsed",
                    ) or ""
                else:
                    responses[question.key] = st.text_input(
                        question.key,
                        value=draft.get(question.key, ""),
                        placeholder=question.uncertainty_option,
                        label_visibility="collapsed",
                    ) or ""
            back, forward = st.columns(2)
            if step_index > 0 and back.form_submit_button("Back"):
                for key, value in responses.items():
                    draft[key] = value.strip()
                st.session_state[step_key] = step_index - 1
                save_world_draft(session, campaign.id, draft, step_index - 1, False)
                st.rerun()
            next_label = "Review world" if step_index == len(steps) - 1 else "Continue"
            if forward.form_submit_button(next_label, type="primary"):
                for key, value in responses.items():
                    draft[key] = value.strip()
                if step_index < len(steps) - 1:
                    st.session_state[step_key] = step_index + 1
                    save_world_draft(session, campaign.id, draft, step_index + 1, False)
                    st.rerun()
                st.session_state[f"world_review_{campaign.id}"] = True
                st.session_state[f"world_review_opened_{campaign.id}"] = True
                save_world_draft(session, campaign.id, draft, step_index, True, True)
                st.rerun()

    world_guidance_panel(session, campaign, current_step, draft)

    if st.session_state.get(f"world_review_{campaign.id}"):
        st.divider()
        st.markdown("<div id='world-review'></div>", unsafe_allow_html=True)
        st.markdown("#### Review before saving")
        if st.session_state.get(f"world_review_opened_{campaign.id}"):
            st.success("Review is open. Your draft is saved locally and ready for acceptance.")
        st.info(
            "This is still a draft. Canonical world records are not changed until you accept it."
        )
        for question in WORLD_QUESTIONS:
            value = draft.get(question.key, question.uncertainty_option)
            st.markdown(f"**{question.prompt}**  \n{value or question.uncertainty_option}")
        st.markdown("#### Readiness checks")
        checks = check_world_draft(draft)
        for check in checks:
            if check.severity == "missing":
                st.error(check.message)
            elif check.severity in ("challenge", "contradiction"):
                st.warning(check.message)
            else:
                st.success(check.message)
        st.download_button(
            "Download world brief",
            build_world_brief(draft, checks),
            file_name=f"{draft.get('world_name', 'world').replace(' ', '-')}.md",
            mime="text/markdown",
            key=f"download_world_{campaign.id}",
        )
        existing_profile = session.scalar(
            select(WorldProfile).where(WorldProfile.campaign_id == campaign.id)
        )
        if existing_profile is not None:
            st.success("This campaign already has an accepted world profile.")
        elif not any(check.severity == "missing" for check in checks) and st.button(
            "Accept world as canonical",
            key=f"accept_world_{campaign.id}",
            type="primary",
        ):
            profile = WorldProfile(
                campaign_id=campaign.id,
                name=draft.get("world_name", "Unnamed world"),
                premise=draft.get("premise", ""),
                mood=draft.get("mood", ""),
                scope=draft.get("scope", ""),
                starting_region=draft.get("starting_region", ""),
                geography=draft.get("geography", ""),
                everyday_life=draft.get("everyday_life", ""),
            )
            profile.history_events.append(
                WorldHistoryEvent(
                    title="The turning point",
                    description=draft.get("turning_point", ""),
                )
            )
            profile.factions.append(
                WorldFaction(
                    name="Initial power structure",
                    public_purpose=draft.get("power_holders", ""),
                )
            )
            profile.magic_rules.append(
                WorldMagicRule(
                    name="The world's fantastic rule",
                    capability=draft.get("fantastic_rule", ""),
                )
            )
            profile.starting_situations.append(
                WorldStartingSituation(
                    title="The campaign begins",
                    problem=draft.get("starting_problem", ""),
                )
            )
            session.add(profile)
            session.commit()
            persisted_draft = session.scalar(
                select(WorldDraft).where(WorldDraft.campaign_id == campaign.id)
            )
            if persisted_draft is not None:
                session.delete(persisted_draft)
                session.commit()
            st.session_state[f"world_accepted_{campaign.id}"] = True
            st.success("World accepted as canonical campaign data.")
            st.rerun()
        if st.button("Start this draft over", key=f"reset_world_{campaign.id}"):
            st.session_state.pop(draft_key, None)
            st.session_state.pop(step_key, None)
            st.session_state.pop(f"world_review_{campaign.id}", None)
            if persisted_draft:
                session.delete(persisted_draft)
                session.commit()
            st.rerun()


def save_world_draft(
    session: Session,
    campaign_id: int,
    draft: dict[str, str],
    current_step: int,
    is_reviewing: bool,
    review_opened: bool = False,
) -> None:
    persisted_draft = session.scalar(
        select(WorldDraft).where(WorldDraft.campaign_id == campaign_id)
    )
    if persisted_draft is None:
        persisted_draft = WorldDraft(campaign_id=campaign_id)
        session.add(persisted_draft)
    saved_draft = dict(draft)
    saved_draft["_review_opened"] = "true" if review_opened else "false"
    persisted_draft.answers_json = json.dumps(saved_draft)
    persisted_draft.current_step = current_step
    persisted_draft.is_reviewing = is_reviewing
    persisted_draft.updated_at = datetime.now()
    session.commit()


def world_guidance_panel(
    session: Session,
    campaign: Campaign,
    step: WorldStep,
    draft: dict[str, str],
) -> None:
    st.divider()
    st.markdown("#### World guide")
    st.caption(
        "Optional intelligence assistance. Suggestions stay in draft state until you accept "
        "the world review."
    )
    mode = st.selectbox(
        "Guide mode",
        WORLD_GUIDANCE_MODES,
        key=f"world_guide_mode_{campaign.id}_{step.value}",
    )
    if st.button("Ask the guide", key=f"world_guide_{campaign.id}_{step.value}"):
        existing_profile = session.scalar(
            select(WorldProfile).where(WorldProfile.campaign_id == campaign.id)
        )
        existing_context = (
            f"{existing_profile.name}: {existing_profile.premise}"
            if existing_profile else ""
        )
        prompt = build_world_guidance_prompt(
            mode=mode,
            step_name=step.value.replace("_", " ").title(),
            answers=draft,
            existing_world=existing_context,
        )
        try:
            with st.spinner("The guide is considering the next thread..."):
                st.session_state[f"world_guide_result_{campaign.id}"] = (
                    OllamaClient(get_settings()).generate(prompt)
                )
        except OllamaError as error:
            st.error(str(error))
    result = st.session_state.get(f"world_guide_result_{campaign.id}")
    if result:
        st.info(result)
        accept, reject = st.columns(2)
        if accept.button("Keep as draft note", key=f"keep_guide_{campaign.id}"):
            notes = draft.get("guidance_notes", "")
            draft["guidance_notes"] = f"{notes}\n{result}".strip()
            st.session_state[f"world_guide_result_{campaign.id}"] = None
            st.success("Suggestion kept in the draft notes.")
        if reject.button("Dismiss suggestion", key=f"dismiss_guide_{campaign.id}"):
            st.session_state[f"world_guide_result_{campaign.id}"] = None
            st.rerun()


def journal_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Journal")
    search = st.text_input("Search entries", placeholder="Title, event, place, or tag")
    with st.form("add_journal", clear_on_submit=True):
        title = st.text_input("Entry title")
        body = st.text_area("What happened?", height=180)
        tags = st.text_input("Tags", placeholder="session-03, Waterdeep, faction")
        if st.form_submit_button("Record event", type="primary") and title.strip() and body.strip():
            session.add(
                JournalEntry(
                    campaign_id=campaign.id, title=title.strip(), body=body.strip(), tags=tags
                )
            )
            session.commit()
            st.rerun()
    entries = list(
        session.scalars(
            select(JournalEntry)
            .where(JournalEntry.campaign_id == campaign.id)
            .order_by(JournalEntry.occurred_at.desc())
        )
    )
    if search.strip():
        needle = search.casefold()
        entries = [
            entry
            for entry in entries
            if needle in " ".join([entry.title, entry.body, entry.tags]).casefold()
        ]
    st.caption(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} shown")
    for entry in entries:
        st.markdown(f"#### {entry.title}")
        st.caption(f"{entry.occurred_at:%Y-%m-%d %H:%M} · {entry.tags or 'untagged'}")
        st.write(entry.body)


def quests_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Quests & objectives")
    status_filter = st.selectbox("Show", ["All statuses", *[item.value for item in QuestStatus]])
    with st.form("add_quest", clear_on_submit=True):
        title = st.text_input("Quest")
        status = st.selectbox("Status", [item.value for item in QuestStatus])
        hook = st.text_area("Hook")
        objective = st.text_area("Objective")
        reward = st.text_input("Reward")
        if st.form_submit_button("Add quest", type="primary") and title.strip():
            session.add(
                Quest(
                    campaign_id=campaign.id,
                    title=title.strip(),
                    status=status,
                    hook=hook,
                    objective=objective,
                    reward=reward,
                )
            )
            session.commit()
            st.rerun()
    quests = campaign_rows(session, Quest, campaign.id)
    if status_filter != "All statuses":
        quests = [quest for quest in quests if quest.status == status_filter]
    st.caption(f"{len(quests)} quest{'s' if len(quests) != 1 else ''} shown")
    for quest in quests:
        with st.expander(f"{quest.title} · {quest.status}"):
            st.write(f"**Hook:** {quest.hook or 'Not set'}")
            st.write(f"**Objective:** {quest.objective or 'Not set'}")
            st.write(f"**Reward:** {quest.reward or 'Not set'}")
    if quests:
        selected = st.selectbox("Open quest builder", quests, format_func=lambda item: item.title)
        quest_workspace(session, campaign, selected)


def quest_workspace(session: Session, campaign: Campaign, quest: Quest) -> None:
    st.markdown(f"### {quest.title} · construction")
    st.caption(
        f"{quest.status} · {len(quest.chapters)} chapters · "
        f"{len(quest.objectives)} objectives"
    )
    blueprint_tab, chapters_tab, links_tab = st.tabs(["Blueprint", "Chapters", "Links"])
    with blueprint_tab:
        with st.form(f"quest_blueprint_{quest.id}"):
            status = st.selectbox("Quest status", [item.value for item in QuestStatus],
                                  index=[item.value for item in QuestStatus].index(quest.status))
            hook = st.text_area("Hook", value=quest.hook)
            through_line = st.text_area("Through-line", value=quest.objective)
            summary_reward = st.text_input("Summary reward", value=quest.reward)
            notes = st.text_area("DM notes", value=quest.notes)
            if st.form_submit_button("Save blueprint", type="primary"):
                quest.status = status
                quest.hook = hook
                quest.objective = through_line
                quest.reward = summary_reward
                quest.notes = notes
                session.commit()
                st.rerun()
        with st.expander("Quest triggers"):
            with st.form(f"quest_trigger_{quest.id}", clear_on_submit=True):
                name = st.text_input("Trigger name")
                trigger_type = st.selectbox("When", [item.value for item in QuestTriggerType])
                condition = st.text_area("Condition")
                effect = st.text_area("Effect")
                if st.form_submit_button("Add trigger") and name.strip():
                    session.add(QuestTrigger(
                        quest=quest, name=name.strip(), trigger_type=trigger_type,
                        condition=condition, effect=effect,
                    ))
                    session.commit()
                    st.rerun()
            for trigger in quest.triggers:
                marker = "fired" if trigger.is_fired else "waiting"
                st.caption(f"{trigger.name} · {trigger.trigger_type} · {marker}")
    with chapters_tab:
        with st.form(f"quest_chapter_{quest.id}", clear_on_submit=True):
            title = st.text_input("Chapter title")
            chapter_status = st.selectbox(
                "Chapter status", [item.value for item in QuestChapterStatus]
            )
            summary = st.text_area("What happens here?")
            dm_notes = st.text_area("DM-only chapter notes")
            if st.form_submit_button("Add chapter") and title.strip():
                session.add(QuestChapter(
                    quest=quest, title=title.strip(), sort_order=len(quest.chapters) + 1,
                    status=chapter_status, summary=summary, dm_notes=dm_notes,
                ))
                session.commit()
                st.rerun()
        if quest.chapters:
            chapter = st.selectbox("Chapter", quest.chapters, format_func=lambda item: item.title)
            with st.expander(f"Add objective to {chapter.title}", expanded=True), st.form(
                f"objective_{chapter.id}", clear_on_submit=True
            ):
                objective_title = st.text_input("Objective title")
                objective_description = st.text_area("Objective details")
                objective_status = st.selectbox(
                    "Objective status", [item.value for item in QuestObjectiveStatus]
                )
                hidden = st.checkbox("Hidden from players")
                if st.form_submit_button("Add objective") and objective_title.strip():
                    session.add(
                        QuestObjective(
                            quest=quest,
                            chapter=chapter,
                            title=objective_title.strip(),
                            description=objective_description,
                            sort_order=len(chapter.objectives) + 1,
                            status=objective_status,
                            is_hidden=hidden,
                        )
                    )
                    session.commit()
                    st.rerun()
            for chapter_objective in chapter.objectives:
                visibility = "hidden" if chapter_objective.is_hidden else "visible"
                st.markdown(
                    f"**{chapter_objective.title}** · "
                    f"{chapter_objective.status} · {visibility}"
                )
                st.caption(chapter_objective.description or "No details recorded.")
        else:
            st.info("Add a chapter to start building the quest path.")
    with links_tab:
        items = campaign_rows(session, Item, campaign.id)
        characters = campaign_rows(session, Character, campaign.id)
        locations = campaign_rows(session, Location, campaign.id)
        with st.form(f"quest_link_{quest.id}"):
            left, right = st.columns(2)
            item = left.selectbox("Required / mentioned item", [None, *items],
                                 format_func=lambda value: "None" if value is None else value.name)
            item_role = left.text_input("Item role", value="Required")
            npc = right.selectbox("NPC / character", [None, *characters],
                                  format_func=lambda value: "None" if value is None else value.name)
            npc_role = right.text_input("NPC role", value="NPC")
            if st.form_submit_button("Add links"):
                if item:
                    session.add(QuestItem(quest=quest, item=item, role=item_role))
                if npc:
                    session.add(QuestCharacter(quest=quest, character=npc, role=npc_role))
                session.commit()
                st.rerun()
        st.markdown("#### Linked entities")
        for item_link in quest.item_links:
            st.write(f"Item · {item_link.item.name} · {item_link.role}")
        for npc_link in quest.npc_links:
            st.write(f"NPC · {npc_link.character.name} · {npc_link.role}")
        if locations:
            st.caption(f"{len(locations)} campaign locations available for future map linking.")
        with st.expander("Add reward"):
            with st.form(f"reward_{quest.id}", clear_on_submit=True):
                title = st.text_input("Reward title")
                description = st.text_area("Reward details")
                experience = st.number_input("Experience points", 0, 999999, 0)
                gold = st.number_input("Gold pieces", 0, 999999, 0)
                if st.form_submit_button("Add reward") and title.strip():
                    session.add(QuestReward(
                        quest=quest, title=title.strip(), description=description,
                        experience_points=experience, gold_pieces=gold,
                    ))
                    session.commit()
                    st.rerun()
            for quest_reward in quest.rewards:
                st.caption(
                    f"{quest_reward.title} · {quest_reward.experience_points} XP · "
                    f"{quest_reward.gold_pieces} gp"
                )


def combat_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Combat tracker")
    encounters = campaign_rows(session, Encounter, campaign.id)
    with st.form("new_encounter", clear_on_submit=True):
        name = st.text_input("Encounter name")
        if st.form_submit_button("Start encounter", type="primary") and name.strip():
            session.add(Encounter(campaign_id=campaign.id, name=name.strip()))
            session.commit()
            st.rerun()
    if not encounters:
        st.info("Start an encounter to build initiative order.")
        return
    encounter = st.selectbox(
        "Encounter", encounters, index=len(encounters) - 1, format_func=lambda item: item.name
    )
    st.write(f"**{encounter.name}** · Round {encounter.round_number}")
    combatants = sorted(encounter.combatants, key=lambda item: item.initiative, reverse=True)
    if combatants:
        active_index = encounter.active_turn % len(combatants)
        active = combatants[active_index]
        st.info(
            f"Current turn: **{active.name}** · Combatant {active_index + 1} of {len(combatants)}"
        )
        if st.button("Advance turn", type="primary"):
            encounter.active_turn += 1
            if encounter.active_turn >= len(combatants):
                encounter.active_turn = 0
                encounter.round_number += 1
            session.commit()
            st.rerun()
    with st.form("add_combatant", clear_on_submit=True):
        columns = st.columns(4)
        name = columns[0].text_input("Combatant")
        initiative = columns[1].number_input("Initiative", -10, 50, 10)
        armor_class = columns[2].number_input("AC", 0, 40, 10)
        hit_points = columns[3].number_input("HP", 1, 999, 10)
        if st.form_submit_button("Add to initiative") and name.strip():
            session.add(
                Combatant(
                    encounter_id=encounter.id,
                    name=name.strip(),
                    initiative=initiative,
                    armor_class=armor_class,
                    max_hp=hit_points,
                    current_hp=hit_points,
                )
            )
            session.commit()
            st.rerun()
    ordered = sorted(encounter.combatants, key=lambda item: item.initiative, reverse=True)
    with st.form("update_combatants"):
        st.markdown("#### Track the fight")
        updates: dict[int, tuple[int, str]] = {}
        for item in ordered:
            columns = st.columns([2, 1, 2])
            columns[0].write(item.name)
            current_hp = columns[1].number_input(
                "HP", 0, item.max_hp, item.current_hp, key=f"hp_{item.id}"
            )
            conditions = columns[2].text_input(
                "Conditions", item.conditions, key=f"conditions_{item.id}"
            )
            updates[item.id] = (current_hp, conditions)
        if ordered and st.form_submit_button("Save combat state"):
            for item in ordered:
                item.current_hp, item.conditions = updates[item.id]
            session.commit()
            st.rerun()
    st.dataframe(
        [
            {
                "Turn": index + 1,
                "Name": item.name,
                "Initiative": item.initiative,
                "AC": item.armor_class,
                "HP": f"{item.current_hp}/{item.max_hp}",
                "Conditions": item.conditions,
            }
            for index, item in enumerate(ordered)
        ],
        use_container_width=True,
        hide_index=True,
    )


def writer_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Session writer")
    settings = get_settings()
    with st.form("generate_script"):
        objective = st.text_area("What should this session accomplish?", height=100)
        columns = st.columns(3)
        tone = columns[0].selectbox(
            "Tone", ["Heroic", "Tense", "Mysterious", "Horror", "Comedic", "Political"]
        )
        pacing = columns[1].selectbox(
            "Pacing", ["Measured", "Escalating", "Relentless", "Open exploration"]
        )
        length = columns[2].selectbox("Length", ["One scene", "Short session", "Full session"])
        model = st.text_input("Ollama model", value=settings.ollama_model)
        extra = st.text_area("Additional direction")
        submitted = st.form_submit_button(
            "Generate script", type="primary", use_container_width=True
        )
    if submitted:
        characters = campaign_rows(session, Character, campaign.id)
        locations = campaign_rows(session, Location, campaign.id)
        quests = [
            item
            for item in campaign_rows(session, Quest, campaign.id)
            if item.status == QuestStatus.ACTIVE
        ]
        events = list(
            session.scalars(
                select(JournalEntry)
                .where(JournalEntry.campaign_id == campaign.id)
                .order_by(JournalEntry.occurred_at.desc())
                .limit(8)
            )
        )
        context = CampaignContext(
            campaign_name=campaign.name,
            campaign_summary=campaign.summary,
            characters=[
                f"{item.name}: {item.kind}, {item.class_name or 'role unknown'}; {item.notes}"
                for item in characters
            ],
            locations=[
                f"{item.name}: {item.description}; secret: {item.secrets}" for item in locations
            ],
            active_quests=[f"{item.title}: {item.objective}" for item in quests],
            recent_events=[f"{item.title}: {item.body}" for item in events],
        )
        prompt = build_session_prompt(
            context,
            objective=objective,
            tone=tone,
            pacing=pacing,
            length=length,
            extra_direction=extra,
        )
        try:
            with st.spinner(f"Consulting {model}…"):
                st.session_state.generated_script = OllamaClient(settings).generate(prompt, model)
        except OllamaError as error:
            st.error(str(error))
    if script := st.session_state.get("generated_script"):
        st.text_area("Generated script", value=script, height=600)
        st.download_button("Download Markdown", script, file_name=f"{campaign.name}-session.md")


def main() -> None:
    render_theme()
    engine = database_engine()
    initialize_database(engine)
    with session_scope(engine) as session:
        workspace = workspace_navigation()
        campaign = campaign_selector(session)
        if campaign is None:
            return
        pages = {
            "The Table": table_page,
            "Party": party_page,
            "World": world_page,
            "Journal": journal_page,
            "Quests": quests_page,
            "Combat": combat_page,
            "Writer": writer_page,
        }
        if workspace == "Briefing":
            dashboard(session, campaign)
        else:
            pages[workspace](session, campaign)


if __name__ == "__main__":
    main()
