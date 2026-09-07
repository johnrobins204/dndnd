import streamlit as st
from sqlalchemy.orm import Session

from dndnd.data.repositories.campaigns import CampaignRepository
from dndnd.models import Campaign

campaigns = CampaignRepository()


def select_campaign(session: Session) -> Campaign:
    campaigns.ensure_starter(session)
    session.commit()
    available = campaigns.list_all(session)

    selected = st.sidebar.selectbox(
        "Campaign", available, format_func=lambda item: item.name
    )
    with (
        st.sidebar.expander("Create campaign"),
        st.form("new_campaign", clear_on_submit=True),
    ):
        name = st.text_input("Campaign name")
        summary = st.text_area("Premise")
        if st.form_submit_button("Create campaign") and name.strip():
            session.add(Campaign(name=name.strip(), summary=summary.strip()))
            session.commit()
            st.rerun()
    return selected
