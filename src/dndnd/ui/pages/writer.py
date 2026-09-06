import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.config import get_settings
from dndnd.intelligence.client import OllamaClient, OllamaError
from dndnd.models import Campaign, Character, JournalEntry, Location, Quest, QuestStatus
from dndnd.prompting import CampaignContext, build_session_prompt


def render(session: Session, campaign: Campaign) -> None:
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
        characters = list(
            session.scalars(select(Character).where(Character.campaign_id == campaign.id))
        )
        locations = list(
            session.scalars(select(Location).where(Location.campaign_id == campaign.id))
        )
        quests = list(
            session.scalars(
                select(Quest).where(
                    Quest.campaign_id == campaign.id, Quest.status == QuestStatus.ACTIVE
                )
            )
        )
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
