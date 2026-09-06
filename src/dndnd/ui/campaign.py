import streamlit as st
from sqlalchemy.orm import Session

from dndnd.data.repositories.campaigns import CampaignRepository
from dndnd.models import Campaign

campaigns = CampaignRepository()


def select_campaign(session: Session) -> Campaign | None:
    available = campaigns.list_all(session)
    if not available:
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
        selected = st.selectbox("Campaign", available, format_func=lambda item: item.name)
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
