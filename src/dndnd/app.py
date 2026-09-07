from typing import Any

import streamlit as st
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from dndnd.config import get_settings
from dndnd.data.repositories.worlds import WorldRepository
from dndnd.db import create_database_engine, initialize_database, session_scope
from dndnd.intelligence.client import OllamaClient, OllamaError
from dndnd.models import (
    Campaign,
    Character,
    Combatant,
    Encounter,
    JournalEntry,
    Location,
    Quest,
    QuestStatus,
)
from dndnd.prompting import (
    CampaignContext,
    build_session_prompt,
)
from dndnd.ui.campaign import select_campaign as render_campaign_context
from dndnd.ui.navigation import workspace_navigation as render_workspace_navigation
from dndnd.ui.pages.briefing import render as render_briefing
from dndnd.ui.pages.combat import render as render_combat_page
from dndnd.ui.pages.journal import render as render_journal_page
from dndnd.ui.pages.party import render as render_party_page
from dndnd.ui.pages.quests import render as render_quests_page
from dndnd.ui.pages.table import render as render_table_page
from dndnd.ui.pages.world import render as render_world_page
from dndnd.ui.pages.writer import render as render_writer_page
from dndnd.ui.theme import render_theme as render_ui_theme

world_repository = WorldRepository()

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


@st.cache_resource
def database_engine() -> Engine:
    engine = create_database_engine()
    initialize_database(engine)
    return engine


def campaign_rows(session: Session, model: Any, campaign_id: int) -> list[Any]:
    return list(session.scalars(select(model).where(model.campaign_id == campaign_id)))


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
        "Encounter",
        encounters,
        index=len(encounters) - 1,
        format_func=lambda item: item.name,
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
                st.session_state.generated_script = OllamaClient(settings).generate(
                    prompt, model=model
                )
        except OllamaError as error:
            st.error(str(error))
    if script := st.session_state.get("generated_script"):
        st.text_area("Generated script", value=script, height=600)
        st.download_button("Download Markdown", script, file_name=f"{campaign.name}-session.md")


def main() -> None:
    render_ui_theme()
    engine = database_engine()
    initialize_database(engine)
    with session_scope(engine) as session:
        campaign = render_campaign_context(session)
        workspace = render_workspace_navigation()
        pages = {
            "The Table": render_table_page,
            "Party": render_party_page,
            "World": render_world_page,
            "Journal": render_journal_page,
            "Quests": render_quests_page,
            "Combat": render_combat_page,
            "Writer": render_writer_page,
        }
        if workspace == "Briefing":
            render_briefing(session, campaign)
        else:
            pages[workspace](session, campaign)


if __name__ == "__main__":
    main()
