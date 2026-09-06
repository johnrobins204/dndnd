import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.models import Campaign, Combatant, Encounter


def render(session: Session, campaign: Campaign) -> None:
    st.subheader("Combat tracker")
    encounters = list(
        session.scalars(select(Encounter).where(Encounter.campaign_id == campaign.id))
    )
    with st.form("new_encounter", clear_on_submit=True):
        name = st.text_input("Encounter name")
        if st.form_submit_button("Start encounter", type="primary") and name.strip():
            session.add(Encounter(campaign_id=campaign.id, name=name.strip()))
            session.commit()
            st.rerun()
    if not encounters:
        st.info("Start an encounter to build initiative order.")
        return
    encounter = st.selectbox(
        "Encounter", encounters, index=len(encounters) - 1, format_func=lambda item: item.name
    )
    st.write(f"**{encounter.name}** · Round {encounter.round_number}")
    combatants = sorted(encounter.combatants, key=lambda item: item.initiative, reverse=True)
    if combatants:
        active_index = encounter.active_turn % len(combatants)
        active = combatants[active_index]
        st.info(
            f"Current turn: **{active.name}** · Combatant {active_index + 1} of {len(combatants)}"
        )
        if st.button("Advance turn", type="primary"):
            encounter.active_turn += 1
            if encounter.active_turn >= len(combatants):
                encounter.active_turn = 0
                encounter.round_number += 1
            session.commit()
            st.rerun()
    with st.form("add_combatant", clear_on_submit=True):
        columns = st.columns(4)
        name = columns[0].text_input("Combatant")
        initiative = columns[1].number_input("Initiative", -10, 50, 10)
        armor_class = columns[2].number_input("AC", 0, 40, 10)
        hit_points = columns[3].number_input("HP", 1, 999, 10)
        if st.form_submit_button("Add to initiative") and name.strip():
            session.add(
                Combatant(
                    encounter_id=encounter.id,
                    name=name.strip(),
                    initiative=initiative,
                    armor_class=armor_class,
                    max_hp=hit_points,
                    current_hp=hit_points,
                )
            )
            session.commit()
            st.rerun()
    ordered = sorted(encounter.combatants, key=lambda item: item.initiative, reverse=True)
    with st.form("update_combatants"):
        st.markdown("#### Track the fight")
        updates: dict[int, tuple[int, str]] = {}
        for item in ordered:
            columns = st.columns([2, 1, 2])
            columns[0].write(item.name)
            current_hp = columns[1].number_input(
                "HP", 0, item.max_hp, item.current_hp, key=f"hp_{item.id}"
            )
            conditions = columns[2].text_input(
                "Conditions", item.conditions, key=f"conditions_{item.id}"
            )
            updates[item.id] = (current_hp, conditions)
        if ordered and st.form_submit_button("Save combat state"):
            for item in ordered:
                item.current_hp, item.conditions = updates[item.id]
            session.commit()
            st.rerun()
    st.dataframe(
        [
            {
                "Turn": index + 1,
                "Name": item.name,
                "Initiative": item.initiative,
                "AC": item.armor_class,
                "HP": f"{item.current_hp}/{item.max_hp}",
                "Conditions": item.conditions,
            }
            for index, item in enumerate(ordered)
        ],
        use_container_width=True,
        hide_index=True,
    )
