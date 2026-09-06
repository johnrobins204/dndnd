from datetime import datetime

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.data.repositories.sessions import SessionRepository
from dndnd.models import (
    Campaign,
    Character,
    Quest,
    QuestStatus,
    SessionEntry,
    SessionEntryKind,
    SessionRun,
    SessionRunStatus,
)

sessions = SessionRepository()


def render(session: Session, campaign: Campaign) -> None:
    st.subheader("The Table")
    st.caption("Run the session, keep the fiction moving, and capture canon as it happens.")
    runs = sessions.list_for_campaign(session, campaign.id)
    with (
        st.expander("Prepare a new session", expanded=not runs),
        st.form("new_session_run", clear_on_submit=True),
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
    left, right = st.columns([3, 1])
    with left:
        st.markdown(f"### {current.title}")
        st.caption(
            f"{current.status} · Scene: {current.current_scene or 'Not set'} · "
            f"{len(current.entries)} transcript entries"
        )
    with right:
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
                    "/scene The drowned archive · /say The bell rings below · "
                    "/note Ask about the sigil"
                ),
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Capture", type="primary", use_container_width=True)
        if submitted and command.strip():
            raw = command.strip()
            lowered = raw.casefold()
            if lowered.startswith("/scene "):
                current.current_scene = raw[7:].strip()
                entry = SessionEntry(kind=SessionEntryKind.SCENE, content=current.current_scene)
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
        characters = list(
            session.scalars(select(Character).where(Character.campaign_id == campaign.id))
        )
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
