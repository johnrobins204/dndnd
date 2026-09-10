import streamlit as st

from dndnd.intelligence.game_chat import PromptStage


@st.dialog("Prompt payload", width="large")
def show_debug_dialog(stages: list[PromptStage], entry_id: int) -> None:
    for index, stage in enumerate(stages):
        st.markdown(f"**{stage.name}** · model `{stage.model}`")
        st.text_area(
            "Prompt",
            stage.prompt,
            height=200,
            disabled=False,
            key=f"debug_prompt_{entry_id}_{index}",
        )
        st.text_area(
            "Raw response",
            stage.raw_response,
            height=150,
            disabled=False,
            key=f"debug_raw_{entry_id}_{index}",
        )
        if stage.parsed_response != stage.raw_response:
            if stage.stripped_preamble:
                st.caption(f"Preamble stripped: {stage.stripped_preamble!r}")
            else:
                st.caption("Cleaned (quotes stripped)")
            st.text_area(
                "Parsed response",
                stage.parsed_response,
                height=150,
                disabled=False,
                key=f"debug_parsed_{entry_id}_{index}",
            )
        if index < len(stages) - 1:
            st.divider()
