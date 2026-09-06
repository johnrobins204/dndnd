from collections.abc import Callable

import streamlit as st

WORKSPACES = ("Briefing", "The Table", "Party", "World", "Journal", "Quests", "Combat", "Writer")


def workspace_navigation() -> str:
    st.sidebar.markdown("### Workspace")
    return st.sidebar.radio(
        "Workspace", WORKSPACES, key="workspace_view", label_visibility="collapsed"
    )


def render_workspace(workspace: str, pages: dict[str, Callable[..., None]], *args: object) -> None:
    if workspace == "Briefing":
        pages["Briefing"](*args)
    else:
        pages[workspace](*args)
