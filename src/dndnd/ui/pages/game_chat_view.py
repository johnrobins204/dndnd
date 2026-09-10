import streamlit as st
from sqlalchemy.orm import Session

import dndnd.models
from dndnd.intelligence.game_chat import (
    VOICE_CONFIGS,
    PromptStage,
    build_turn_summary,
)


def render_game_chat(
    session: Session, game: dndnd.models.Game, session_run: dndnd.models.SessionRun
) -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        .block-container { padding-bottom: 7rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    exit_column, title_column = st.columns([1, 5])
    if exit_column.button("Exit game"):
        st.session_state.pop("active_game_id", None)
        st.rerun()
    title_column.subheader(game.name)
    selected_names = [link.character.name for link in game.character_links] or [game.character.name]
    quest_label = f" · {game.quest.title}" if game.quest else ""
    title_column.caption(f"{game.campaign.name}{quest_label} · {', '.join(selected_names)}")

    _render_turn_summary(build_turn_summary(game=game, session_run=session_run))

    voice_col, debug_col = st.columns([3, 1])
    voice_key = voice_col.selectbox(
        "Voice",
        list(VOICE_CONFIGS),
        format_func=lambda key: VOICE_CONFIGS[key].label,
        key=f"game_voice_{game.id}",
    )
    debug_mode = debug_col.toggle("Debug", key=f"debug_mode_{game.id}", value=False)

    debug_stage_map: dict[int, list[PromptStage]] = st.session_state.setdefault(
        f"debug_stages_{game.id}", {}
    )

    for entry in session_run.entries:
        if entry.kind == dndnd.models.SessionEntryKind.CHAT_INPUT:
            st.chat_message("user").write(entry.content)
        elif entry.kind == dndnd.models.SessionEntryKind.CHAT_OUTPUT:
            st.chat_message("assistant").write(entry.content)
            if (
                debug_mode
                and entry.id in debug_stage_map
                and st.button(
                    "View prompt payload",
                    key=f"debug_btn_{entry.id}",
                )
            ):
                show_debug_dialog(debug_stage_map[entry.id], entry_id=entry.id)
        else:
            st.caption(f"{entry.kind}: {entry.content}")

    user_input = st.chat_input("Send a prompt. Use / to access tools.")
    if user_input:
        kind, payload = route_input(user_input)

        if kind == "tool":
            response, stages = run_tool(
                payload,
                session=session,
                game=game,
                session_run=session_run,
            )
        else:
            response, stages = run_normal_chat(
                payload,
                session=session,
                game=game,
                session_run=session_run,
                voice_key=voice_key,
            )

        chat_input_entry = dndnd.models.SessionEntry(
            kind=dndnd.models.SessionEntryKind.CHAT_INPUT,
            content=user_input,
        )
        chat_output_entry = dndnd.models.SessionEntry(
            kind=dndnd.models.SessionEntryKind.CHAT_OUTPUT,
            content=response,
        )
        session_run.entries.append(chat_input_entry)
        session_run.entries.append(chat_output_entry)
        session.commit()

        if stages:
            debug_stage_map[chat_output_entry.id] = stages
            while len(debug_stage_map) > 20:
                debug_stage_map.pop(next(iter(debug_stage_map)))

        st.session_state["active_game_id"] = game.id
        st.rerun()


def render(session: Session, campaign: dndnd.models.Campaign) -> None:
    active_game_id = st.session_state.get("active_game_id")
    if active_game_id is not None:
        active_game = games.get_active(session, int(active_game_id))
        if active_game is not None:
            session_run = sessions.get_or_create_active_for_game(session, active_game)
            session.commit()
            render_game_chat(session, active_game, session_run)
            return
        st.session_state.pop("active_game_id", None)

    st.subheader("The Table")
    st.caption("Start from the campaign and party roster before opening a game flow.")

    campaign_rows = campaign.list_all(session)
    character_rows = characters.list_for_campaign(session, campaign.id)
    active_games = games.list_active(session)
    character_options = games.list_character_options_for_campaign(session, campaign.id)

    st.markdown("#### Campaigns")
    st.dataframe(
        [
            {
                "Campaign": item.name,
                "System": item.system,
                "Selected": "Yes" if item.id == campaign.id else "",
            }
            for item in campaign_rows
        ],
        width="stretch",
        hide_index=True,
    )

    st.markdown("#### Characters")
    if character_rows:
        st.dataframe(
            [
                {
                    "Character": item.name,
                    "Type": item.kind,
                    "Class / role": item.class_name or "Unset",
                    "Level": item.level,
                    "HP": f"{item.current_hp}/{item.max_hp}",
                }
                for item in character_rows
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No characters yet. The Party workspace can add the first one.")

    st.markdown("#### Game desk")
    new_game_key = "table_new_game_open"
    if active_games:
        active_games_by_id = {game.id: game for game in active_games}
        selected_game_id = st.selectbox(
            "Active game",
            list(active_games_by_id),
            index=None,
            placeholder="Choose an active game",
            format_func=lambda game_id: active_game_label(active_games_by_id[game_id]),
        )
        start, new = st.columns(2)
        if start.button(
            "Start game",
            type="primary",
            disabled=selected_game_id is None,
            width="stretch",
        ):
            st.session_state["active_game_id"] = selected_game_id
            st.rerun()
        if new.button("New game", width="stretch"):
            st.session_state[new_game_key] = True
            st.rerun()
    elif st.button("New game", type="primary"):
        st.session_state[new_game_key] = True
        st.rerun()

    if st.session_state.get(new_game_key):
        with st.form("new_game"):
            name = st.text_input("Game name")
            quest_options = games.list_quest_options_for_campaign(session, campaign.id)
            quest_options_by_key = {option.key: option for option in quest_options}
            character_options_by_key = {option.key: option for option in character_options}
            selected_quest_key = st.selectbox(
                "Quest",
                [None, *list(quest_options_by_key)],
                format_func=lambda key: (
                    "No quest" if key is None else quest_options_by_key[key].label
                ),
            )
            selected_character_keys = st.multiselect(
                "Characters",
                list(character_options_by_key),
                format_func=lambda key: character_options_by_key[key].label,
                default=list(character_options_by_key)[:1],
                disabled=not character_options_by_key,
            )
            submitted = st.form_submit_button("Create game", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Game name is required.")
                elif not selected_character_keys:
                    st.error("Select at least one character before starting a game.")
                else:
                    selected_characters = [
                        character_options_by_key[key] for key in selected_character_keys
                    ]
                    quest_id = (
                        quest_options_by_key[selected_quest_key].quest_id
                        if selected_quest_key is not None
                        else None
                    )
                    games.create(
                        session,
                        name=name.strip(),
                        campaign_id=campaign.id,
                        character_id=selected_characters[0].character_id,
                        character_ids=[character.character_id for character in selected_characters],
                        quest_id=quest_id,
                    )
                    session.commit()
                    st.session_state[new_game_key] = False
                    st.rerun()
