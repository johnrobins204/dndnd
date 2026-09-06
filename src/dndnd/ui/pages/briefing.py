from typing import Any

import streamlit as st
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dndnd.models import Campaign, Character, JournalEntry, Location, Quest, QuestStatus
from dndnd.ui.theme import render_campaign_briefing


def _campaign_count(session: Session, model: Any, campaign_id: int) -> int:
    return (
        session.scalar(
            select(func.count()).select_from(model).where(model.campaign_id == campaign_id)
        )
        or 0
    )


def render(session: Session, campaign: Campaign) -> None:
    render_campaign_briefing(campaign)
    columns = st.columns(4)
    for column, model, label in zip(
        columns,
        [Character, Location, Quest, JournalEntry],
        ["Characters", "Locations", "Quests", "Journal entries"],
        strict=True,
    ):
        column.metric(label, _campaign_count(session, model, campaign.id))
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
            st.info("No active quests yet. Add the first thread from the Quests workspace.")
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
