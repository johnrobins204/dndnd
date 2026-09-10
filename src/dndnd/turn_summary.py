import streamlit as st

from dndnd.intelligence.game_chat import TurnSummary


def _render_turn_summary(summary: TurnSummary) -> None:
    with st.container(border=True):
        meta_col, quest_col = st.columns([1, 2])
        meta_col.metric("Turn", summary.turn_number)
        meta_col.caption(f"Scene: {summary.scene}")
        quest_col.markdown(f"**Quest:** {summary.quest_title or 'None'}")
        quest_col.caption(summary.quest_goal)

        party = summary.party
        if not party:
            st.caption("No party members selected.")
            return
        chunk_size = 6
        for start in range(0, len(party), chunk_size):
            chunk = party[start : start + chunk_size]
            cols = st.columns(len(chunk))
            for col, member in zip(cols, chunk, strict=False):
                col.metric(
                    member.name,
                    f"{member.current_hp}/{member.max_hp} HP",
                    member.condition,
                )
