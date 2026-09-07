"""Quest page and quest builder workflows."""

import streamlit as st
from sqlalchemy.orm import Session

from dndnd.data.repositories.quests import QuestRepository
from dndnd.models import (
    Campaign,
    Quest,
    QuestChapter,
    QuestChapterStatus,
    QuestCharacter,
    QuestItem,
    QuestObjective,
    QuestObjectiveStatus,
    QuestReward,
    QuestStatus,
    QuestTrigger,
    QuestTriggerType,
)

quest_repository = QuestRepository()


def render(session: Session, campaign: Campaign) -> None:
    st.subheader("Quests & objectives")
    status_filter = st.selectbox(
        "Show", ["All statuses", *[item.value for item in QuestStatus]]
    )
    with st.form("add_quest", clear_on_submit=True):
        title = st.text_input("Quest")
        status = st.selectbox("Status", [item.value for item in QuestStatus])
        hook = st.text_area("Hook")
        objective = st.text_area("Objective")
        reward = st.text_input("Reward")
        if st.form_submit_button("Add quest", type="primary") and title.strip():
            session.add(
                Quest(
                    campaign_id=campaign.id,
                    title=title.strip(),
                    status=status,
                    hook=hook,
                    objective=objective,
                    reward=reward,
                )
            )
            session.commit()
            st.rerun()
    quests = quest_repository.list_for_campaign(session, campaign.id)
    if status_filter != "All statuses":
        quests = [quest for quest in quests if quest.status == status_filter]
    st.caption(f"{len(quests)} quest{'s' if len(quests) != 1 else ''} shown")
    for quest in quests:
        with st.expander(f"{quest.title} · {quest.status}"):
            st.write(f"**Hook:** {quest.hook or 'Not set'}")
            st.write(f"**Objective:** {quest.objective or 'Not set'}")
            st.write(f"**Reward:** {quest.reward or 'Not set'}")
    if quests:
        selected = st.selectbox(
            "Open quest builder", quests, format_func=lambda item: item.title
        )
        quest = quest_repository.get_builder(session, selected.id) or selected
        quest_workspace(session, campaign, quest)


def quest_workspace(session: Session, campaign: Campaign, quest: Quest) -> None:
    st.markdown(f"### {quest.title} · construction")
    st.caption(
        f"{quest.status} · {len(quest.chapters)} chapters · {len(quest.objectives)} objectives"
    )
    blueprint_tab, chapters_tab, links_tab = st.tabs(["Blueprint", "Chapters", "Links"])
    with blueprint_tab:
        with st.form(f"quest_blueprint_{quest.id}"):
            status = st.selectbox(
                "Quest status",
                [item.value for item in QuestStatus],
                index=[item.value for item in QuestStatus].index(quest.status),
            )
            hook = st.text_area("Hook", value=quest.hook)
            through_line = st.text_area("Through-line", value=quest.objective)
            summary_reward = st.text_input("Summary reward", value=quest.reward)
            notes = st.text_area("DM notes", value=quest.notes)
            if st.form_submit_button("Save blueprint", type="primary"):
                quest.status = status
                quest.hook = hook
                quest.objective = through_line
                quest.reward = summary_reward
                quest.notes = notes
                session.commit()
                st.rerun()
        with st.expander("Quest triggers"):
            with st.form(f"quest_trigger_{quest.id}", clear_on_submit=True):
                name = st.text_input("Trigger name")
                trigger_type = st.selectbox(
                    "When", [item.value for item in QuestTriggerType]
                )
                condition = st.text_area("Condition")
                effect = st.text_area("Effect")
                if st.form_submit_button("Add trigger") and name.strip():
                    session.add(
                        QuestTrigger(
                            quest=quest,
                            name=name.strip(),
                            trigger_type=trigger_type,
                            condition=condition,
                            effect=effect,
                        )
                    )
                    session.commit()
                    st.rerun()
            for trigger in quest.triggers:
                marker = "fired" if trigger.is_fired else "waiting"
                st.caption(f"{trigger.name} · {trigger.trigger_type} · {marker}")
    with chapters_tab:
        with st.form(f"quest_chapter_{quest.id}", clear_on_submit=True):
            title = st.text_input("Chapter title")
            chapter_status = st.selectbox(
                "Chapter status", [item.value for item in QuestChapterStatus]
            )
            summary = st.text_area("What happens here?")
            dm_notes = st.text_area("DM-only chapter notes")
            if st.form_submit_button("Add chapter") and title.strip():
                session.add(
                    QuestChapter(
                        quest=quest,
                        title=title.strip(),
                        sort_order=len(quest.chapters) + 1,
                        status=chapter_status,
                        summary=summary,
                        dm_notes=dm_notes,
                    )
                )
                session.commit()
                st.rerun()
        if quest.chapters:
            chapter = st.selectbox(
                "Chapter", quest.chapters, format_func=lambda item: item.title
            )
            with (
                st.expander(f"Add objective to {chapter.title}", expanded=True),
                st.form(f"objective_{chapter.id}", clear_on_submit=True),
            ):
                objective_title = st.text_input("Objective title")
                objective_description = st.text_area("Objective details")
                objective_status = st.selectbox(
                    "Objective status", [item.value for item in QuestObjectiveStatus]
                )
                hidden = st.checkbox("Hidden from players")
                if st.form_submit_button("Add objective") and objective_title.strip():
                    session.add(
                        QuestObjective(
                            quest=quest,
                            chapter=chapter,
                            title=objective_title.strip(),
                            description=objective_description,
                            sort_order=len(chapter.objectives) + 1,
                            status=objective_status,
                            is_hidden=hidden,
                        )
                    )
                    session.commit()
                    st.rerun()
            for chapter_objective in chapter.objectives:
                visibility = "hidden" if chapter_objective.is_hidden else "visible"
                st.markdown(
                    f"**{chapter_objective.title}** · {chapter_objective.status} · {visibility}"
                )
                st.caption(chapter_objective.description or "No details recorded.")
        else:
            st.info("Add a chapter to start building the quest path.")
    with links_tab:
        items = quest_repository.list_items_for_campaign(session, campaign.id)
        characters = quest_repository.list_characters_for_campaign(session, campaign.id)
        locations = quest_repository.list_locations_for_campaign(session, campaign.id)
        with st.form(f"quest_link_{quest.id}"):
            left, right = st.columns(2)
            item = left.selectbox(
                "Required / mentioned item",
                [None, *items],
                format_func=lambda value: "None" if value is None else value.name,
            )
            item_role = left.text_input("Item role", value="Required")
            npc = right.selectbox(
                "NPC / character",
                [None, *characters],
                format_func=lambda value: "None" if value is None else value.name,
            )
            npc_role = right.text_input("NPC role", value="NPC")
            if st.form_submit_button("Add links"):
                if item:
                    session.add(QuestItem(quest=quest, item=item, role=item_role))
                if npc:
                    session.add(
                        QuestCharacter(quest=quest, character=npc, role=npc_role)
                    )
                session.commit()
                st.rerun()
        st.markdown("#### Linked entities")
        for item_link in quest.item_links:
            st.write(f"Item · {item_link.item.name} · {item_link.role}")
        for npc_link in quest.npc_links:
            st.write(f"NPC · {npc_link.character.name} · {npc_link.role}")
        if locations:
            st.caption(
                f"{len(locations)} campaign locations available for future map linking."
            )
        with st.expander("Add reward"):
            with st.form(f"reward_{quest.id}", clear_on_submit=True):
                title = st.text_input("Reward title")
                description = st.text_area("Reward details")
                experience = st.number_input("Experience points", 0, 999999, 0)
                gold = st.number_input("Gold pieces", 0, 999999, 0)
                if st.form_submit_button("Add reward") and title.strip():
                    session.add(
                        QuestReward(
                            quest=quest,
                            title=title.strip(),
                            description=description,
                            experience_points=experience,
                            gold_pieces=gold,
                        )
                    )
                    session.commit()
                    st.rerun()
            for quest_reward in quest.rewards:
                st.caption(
                    f"{quest_reward.title} · {quest_reward.experience_points} XP · "
                    f"{quest_reward.gold_pieces} gp"
                )
