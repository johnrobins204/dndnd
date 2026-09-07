from collections.abc import Callable

import streamlit as st

WORKSPACES = (
    "Briefing",
    "The Table",
    "Party",
    "World",
    "Journal",
    "Quests",
    "Combat",
    "Writer",
)


def workspace_navigation() -> str:
    st.sidebar.markdown("### Workspace")
    current = st.session_state.get("workspace_view", WORKSPACES[0])
    if current not in WORKSPACES:
        current = WORKSPACES[0]
        st.session_state["workspace_view"] = current

    for workspace in WORKSPACES:
        if st.sidebar.button(
            workspace,
            key=f"workspace_nav_{workspace}",
            type="primary" if workspace == current else "secondary",
            use_container_width=True,
        ):
            st.session_state["workspace_view"] = workspace
            st.rerun()

    return str(current)


def render_workspace(
    workspace: str, pages: dict[str, Callable[..., None]], *args: object
) -> None:
    if workspace == "Briefing":
        pages["Briefing"](*args)
    else:
        pages[workspace](*args)
