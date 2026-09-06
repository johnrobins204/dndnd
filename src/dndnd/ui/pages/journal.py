import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.models import Campaign, JournalEntry


def render(session: Session, campaign: Campaign) -> None:
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
