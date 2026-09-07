"""Party page and guided character creation workflows."""

import random
import time
from html import escape
from typing import Any, cast

import streamlit as st
from sqlalchemy.orm import Session

from dndnd.data.repositories.characters import CharacterRepository
from dndnd.domain.characters import (
    POINT_BUY_BUDGET,
    AbilityScoreMethod,
    CharacterDraft,
    ability_modifier,
    build_random_draft,
    derive_values,
    validate_draft,
)
from dndnd.domain.characters import (
    generate_ability_scores as domain_generate_ability_scores,
)
from dndnd.domain.characters import (
    point_buy_total as domain_point_buy_total,
)
from dndnd.models import (
    Alignment,
    Campaign,
    Character,
    CharacterAncestry,
    CharacterClass,
    CharacterFeature,
    CharacterJournalEntry,
    CharacterKind,
    CharacterSheet,
    InventoryItem,
    Item,
    ItemKind,
    Player,
)
from dndnd.rules import (
    ANCESTRY_REFERENCES,
    CLASS_REFERENCES,
    COMBAT_RULES_REFERENCE,
    RuleReference,
)

character_repository = CharacterRepository()


ABILITY_NAMES = [
    "Strength",
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma",
]
DICE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]


_METHOD_LABELS: dict[str, AbilityScoreMethod] = {
    "Standard array": AbilityScoreMethod.STANDARD_ARRAY,
    "Dice roll (4d6, drop lowest)": AbilityScoreMethod.DICE_4D6_DROP_LOWEST,
    "Point buy final scores": AbilityScoreMethod.POINT_BUY,
    "Manual entry": AbilityScoreMethod.MANUAL,
}


def random_character_draft(existing_names: set[str], players: list[Player]) -> dict[str, Any]:
    rng = random.Random()
    draft = build_random_draft(existing_names, players, rng)
    return _draft_to_dict(draft)


def _draft_to_dict(draft: CharacterDraft) -> dict[str, Any]:
    return {
        "name": draft.name,
        "kind": draft.kind,
        "player_id": draft.player_id,
        "ancestry": draft.ancestry,
        "class_name": draft.class_name,
        "level": draft.level,
        "background": draft.background,
        "alignment": draft.alignment,
        "concept": draft.concept,
        "ability_values": dict(draft.ability_scores),
        "ability_method": draft.ability_method,
        "armor_class": draft.derived.armor_class,
        "max_hp": draft.derived.max_hp,
        "speed": draft.derived.speed,
        "proficiency_bonus": draft.derived.proficiency_bonus,
        "passive_perception": draft.derived.passive_perception,
        "hit_dice": draft.derived.hit_dice,
        "spellcasting_ability": draft.derived.spellcasting_ability,
        "feature_lines": "\n".join(draft.feature_lines),
        "notes": draft.notes,
    }


def generate_ability_scores(method: str) -> dict[str, int]:
    ability_method = _METHOD_LABELS.get(method, AbilityScoreMethod.DICE_4D6_DROP_LOWEST)
    rng = random.Random()
    return domain_generate_ability_scores(ability_method, rng)


def _render_preview_card(draft: dict[str, Any]) -> None:
    st.markdown("#### Preview")
    identity = st.columns(4)
    identity[0].metric("Name", draft.get("name", "—"))
    identity[1].metric("Ancestry", draft.get("ancestry", "—"))
    identity[2].metric("Class", draft.get("class_name", "—"))
    identity[3].metric("Background", draft.get("background", "—") or "—")
    ability_values = draft.get("ability_values", {})
    ability_columns = st.columns(6)
    for column, ability_name in zip(ability_columns, ABILITY_NAMES, strict=True):
        score = ability_values.get(ability_name, 10)
        column.metric(
            ability_name[:3].upper(),
            score,
            f"{ability_modifier(score):+d}",
        )
    rules = st.columns(5)
    rules[0].metric("AC", draft.get("armor_class", "—"))
    rules[1].metric("Max HP", draft.get("max_hp", "—"))
    rules[2].metric("Speed", draft.get("speed", "—"))
    rules[3].metric("Prof. Bonus", draft.get("proficiency_bonus", "—"))
    rules[4].metric("Passive Perception", draft.get("passive_perception", "—"))
    hit_dice = draft.get("hit_dice", "—")
    spellcasting = draft.get("spellcasting_ability") or "None"
    st.caption(f"Hit dice: {hit_dice} · Spellcasting: {spellcasting}")


def _regenerate_draft(
    existing_names: set[str],
    players: list[Player],
    draft: dict[str, Any],
    lock_identity: bool,
    lock_abilities: bool,
) -> dict[str, Any]:
    rng = random.Random()
    fresh = _draft_to_dict(build_random_draft(existing_names, players, rng))
    if lock_identity:
        identity_keys = [
            "name",
            "kind",
            "player_id",
            "ancestry",
            "class_name",
            "background",
            "alignment",
            "concept",
        ]
        for key in identity_keys:
            fresh[key] = draft.get(key, fresh[key])
    if lock_abilities:
        fresh["ability_values"] = dict(draft.get("ability_values", {}))
        fresh["ability_method"] = draft.get("ability_method", fresh["ability_method"])
    return fresh


def build_roll_board(
    method: str,
    landed_scores: dict[str, int],
    active_name: str | None = None,
    active_frame: int = 0,
    active_phase: str = "rolling",
) -> list[str]:
    board = [f"### Ability score roll · {method}", ""]
    for ability_index, ability_name in enumerate(ABILITY_NAMES):
        if ability_name in landed_scores:
            board.append(f"✅ **{ability_name}** · **{landed_scores[ability_name]}**")
        elif ability_name == active_name:
            face = DICE_FACES[(ability_index + active_frame) % len(DICE_FACES)]
            board.append(f"{face} **{ability_name}** · {active_phase}...")
        else:
            board.append(f"○ **{ability_name}** · waiting")
    return board


def render_roll_board(
    animation: Any,
    method: str,
    landed_scores: dict[str, int],
    active_name: str | None = None,
    active_frame: int = 0,
    active_phase: str = "rolling",
) -> None:
    animation.markdown(
        "\n\n".join(
            build_roll_board(method, landed_scores, active_name, active_frame, active_phase)
        )
    )


def animate_ability_scores(
    method: str, target_scores: dict[str, int] | None = None
) -> dict[str, int]:
    scores = target_scores if target_scores is not None else generate_ability_scores(method)
    animation = st.empty()
    progress = st.progress(0, text="The dice are in motion...")
    landed_scores: dict[str, int] = {}
    for ability_index, ability_name in enumerate(ABILITY_NAMES):
        for frame_index in range(6):
            render_roll_board(
                animation, method, landed_scores, ability_name, frame_index, "rolling"
            )
            time.sleep(0.08)
        render_roll_board(animation, method, landed_scores, ability_name, 5, "lands")
        time.sleep(0.12)
        landed_scores[ability_name] = scores[ability_name]
        render_roll_board(animation, method, landed_scores)
        progress.progress(
            (ability_index + 1) / len(ABILITY_NAMES),
            text=f"{ability_name} locked in",
        )
        time.sleep(0.1)
    render_roll_board(animation, method, landed_scores)
    return scores


def alignment_grid(current: str, widget_key: str) -> str:
    st.markdown("**Alignment**")
    st.caption("Optional. Choose a cell or leave alignment unset.")
    rows = [
        [Alignment.LAWFUL_GOOD, Alignment.NEUTRAL_GOOD, Alignment.CHAOTIC_GOOD],
        [Alignment.LAWFUL_NEUTRAL, Alignment.TRUE_NEUTRAL, Alignment.CHAOTIC_NEUTRAL],
        [Alignment.LAWFUL_EVIL, Alignment.NEUTRAL_EVIL, Alignment.CHAOTIC_EVIL],
    ]
    selected = cast(str, st.session_state.get(widget_key, current))
    for row_index, row in enumerate(rows):
        columns = st.columns(3)
        for column, alignment in zip(columns, row, strict=True):
            if column.button(
                alignment.value,
                key=f"{widget_key}_{row_index}_{alignment.value}",
                type="primary" if selected == alignment.value else "secondary",
                use_container_width=True,
            ):
                st.session_state[widget_key] = alignment.value
                st.rerun()
    st.caption(f"Selected: {selected or 'Not set'}")
    return selected


def render_rule_reference(reference: RuleReference, key: str) -> None:
    official_link = (
        f"<a href='{escape(reference.official_url)}' target='_blank' rel='noreferrer'>"
        "Official 2024 rules ↗</a> · "
        if reference.official_url
        else ""
    )
    st.markdown(
        f"<div class='empty-callout' key='{escape(key)}'>"
        f"<strong>{escape(reference.name)}</strong><br>{escape(reference.summary)}<br>"
        f"{official_link}"
        f"<a href='{escape(reference.wiki_url)}' target='_blank' rel='noreferrer'>"
        "Read the reference wiki ↗</a></div>",
        unsafe_allow_html=True,
    )


def character_workspace(session: Session, campaign: Campaign, character: Character) -> None:
    st.markdown(f"### {character.name}")
    st.caption(
        f"{character.ancestry or 'Ancestry unset'} · {character.class_name or 'Role unset'} · "
        f"Level {character.level} · {character.current_hp}/{character.max_hp} HP"
    )
    sheet_tab, journal_tab, inventory_tab, features_tab = st.tabs(
        ["Sheet", "Character journal", "Inventory", "Features"]
    )
    with sheet_tab:
        render_character_sheet(character)
        sheet = character.sheet
        alignment = alignment_grid(
            sheet.alignment if sheet else "", f"alignment_sheet_{character.id}"
        )
        with st.form(f"sheet_{character.id}"):
            left, middle, right = st.columns(3)
            background = left.text_input("Background", value=sheet.background if sheet else "")
            experience = left.number_input(
                "Experience points", 0, 999999, sheet.experience_points if sheet else 0
            )
            temporary_hp = middle.number_input(
                "Temporary HP", 0, 999, sheet.temporary_hp if sheet else 0
            )
            hit_dice = middle.text_input("Hit dice", value=sheet.hit_dice if sheet else "")
            speed = middle.number_input("Speed", 0, 200, sheet.speed if sheet else 30)
            right.metric("Proficiency bonus", sheet.proficiency_bonus if sheet else 2)
            right.metric("Passive perception", sheet.passive_perception if sheet else 10)
            inspiration = right.checkbox("Inspiration", value=sheet.inspiration if sheet else False)
            spellcasting = st.text_input(
                "Spellcasting ability",
                value=sheet.spellcasting_ability if sheet else "",
            )
            notes = st.text_area("Sheet notes", value=sheet.notes if sheet else "")
            if st.form_submit_button("Save sheet", type="primary"):
                if sheet is None:
                    sheet = CharacterSheet(character=character)
                    session.add(sheet)
                sheet.background = background
                sheet.alignment = alignment
                sheet.experience_points = experience
                sheet.temporary_hp = temporary_hp
                sheet.hit_dice = hit_dice
                sheet.speed = speed
                sheet.inspiration = inspiration
                sheet.spellcasting_ability = spellcasting
                sheet.notes = notes
                session.commit()
                st.rerun()
    with journal_tab:
        with st.form(f"character_journal_{character.id}", clear_on_submit=True):
            title = st.text_input("Entry title")
            kind = st.selectbox("Entry type", ["Memory", "Secret", "Relationship", "Goal", "Note"])
            body = st.text_area("Entry", height=140)
            session_number = st.number_input("Session", 0, 9999, 0)
            private = st.checkbox("DM-only", value=True)
            tags = st.text_input("Tags")
            if st.form_submit_button("Add character entry") and title.strip() and body.strip():
                session.add(
                    CharacterJournalEntry(
                        character=character,
                        title=title.strip(),
                        kind=kind,
                        body=body.strip(),
                        session_number=session_number or None,
                        is_private=private,
                        tags=tags,
                    )
                )
                session.commit()
                st.rerun()
        for entry in sorted(
            character.journal_entries, key=lambda item: item.created_at, reverse=True
        ):
            label = "DM-only" if entry.is_private else "table-visible"
            with st.expander(f"{entry.title} · {entry.kind} · {label}"):
                st.caption(
                    f"Session {entry.session_number or 'unspecified'} · {entry.tags or 'untagged'}"
                )
                st.write(entry.body)
    with inventory_tab:
        items = character_repository.list_items_for_campaign(session, campaign.id)
        with (
            st.expander("Create campaign item"),
            st.form(f"new_item_{character.id}", clear_on_submit=True),
        ):
            item_name = st.text_input("Item name")
            item_kind = st.selectbox("Item type", [item.value for item in ItemKind])
            description = st.text_area("Description")
            rarity = st.text_input("Rarity")
            if st.form_submit_button("Create item") and item_name.strip():
                session.add(
                    Item(
                        campaign_id=campaign.id,
                        name=item_name.strip(),
                        kind=item_kind,
                        description=description,
                        rarity=rarity,
                    )
                )
                session.commit()
                st.rerun()
        if items:
            with st.form(f"inventory_{character.id}", clear_on_submit=True):
                item = st.selectbox("Item", items, format_func=lambda value: value.name)
                quantity = st.number_input("Quantity", 1, 999, 1)
                equipped = st.checkbox("Equipped")
                attuned = st.checkbox("Attuned")
                notes = st.text_input("Inventory notes")
                if st.form_submit_button("Add to inventory"):
                    session.add(
                        InventoryItem(
                            character=character,
                            item=item,
                            quantity=quantity,
                            equipped=equipped,
                            attuned=attuned,
                            notes=notes,
                        )
                    )
                    session.commit()
                    st.rerun()
        else:
            st.info("Create a campaign item before adding inventory.")
        st.dataframe(
            [
                {
                    "Item": entry.custom_name
                    or (entry.item.name if entry.item else "Unlinked item"),
                    "Qty": entry.quantity,
                    "Equipped": entry.equipped,
                    "Attuned": entry.attuned,
                    "Notes": entry.notes,
                }
                for entry in character.inventory
            ],
            use_container_width=True,
            hide_index=True,
        )
    with features_tab:
        with st.form(f"feature_{character.id}", clear_on_submit=True):
            name = st.text_input("Feature name")
            category = st.text_input("Category", value="Feature")
            source = st.text_input("Source")
            description = st.text_area("Rules text / DM reminder")
            uses_max = st.number_input("Uses", 0, 99, 0)
            if st.form_submit_button("Add feature") and name.strip():
                session.add(
                    CharacterFeature(
                        character=character,
                        name=name.strip(),
                        category=category,
                        source=source,
                        description=description,
                        uses_max=uses_max or None,
                        uses_remaining=uses_max or None,
                    )
                )
                session.commit()
                st.rerun()
        for feature in character.features:
            st.markdown(f"**{feature.name}** · {feature.category}")
            st.caption(feature.source or "No source recorded")
            st.write(feature.description or "No description recorded.")


def new_character_interview(session: Session, campaign: Campaign, players: list[Player]) -> None:
    draft_key = f"character_draft_{campaign.id}"
    step_key = f"character_step_{campaign.id}"
    draft: dict[str, Any] = st.session_state.setdefault(draft_key, {})
    step = st.session_state.get(step_key, 1)
    existing_names = {
        character.name for character in character_repository.list_for_campaign(session, campaign.id)
    }
    st.markdown("### New Character")
    st.caption("A guided pass from character concept to engine-ready sheet data.")
    st.progress((step - 1) / 4, text=f"Step {step} of 4")

    if step == 1:
        st.markdown("#### 1 · Identity and concept")
        st.write("Start with the character the player wants to bring to the table.")
        if st.button("🎲 Roll random character", key=f"random_character_{campaign.id}"):
            draft.clear()
            draft.update(random_character_draft(existing_names, players))
            draft["ability_method"] = "Dice roll (4d6, drop lowest)"
            draft["ability_values"] = animate_ability_scores(
                draft["ability_method"], draft.get("ability_values")
            )
            st.session_state[f"alignment_interview_{campaign.id}"] = draft["alignment"]
            st.session_state[f"interview_ancestry_{campaign.id}"] = draft["ancestry"]
            st.session_state[f"interview_class_{campaign.id}"] = draft["class_name"]
            st.rerun()
        alignment = alignment_grid(draft.get("alignment", ""), f"alignment_interview_{campaign.id}")
        ancestry_options = [item.value for item in CharacterAncestry]
        class_options = [item.value for item in CharacterClass]
        ancestry = st.selectbox(
            "Species / ancestry",
            ancestry_options,
            index=(
                ancestry_options.index(draft["ancestry"])
                if draft.get("ancestry") in ancestry_options
                else 0
            ),
            key=f"interview_ancestry_{campaign.id}",
        )
        render_rule_reference(ANCESTRY_REFERENCES[ancestry], "ancestry_reference")
        class_name = st.selectbox(
            "Class",
            class_options,
            index=(
                class_options.index(draft["class_name"])
                if draft.get("class_name") in class_options
                else 0
            ),
            key=f"interview_class_{campaign.id}",
        )
        render_rule_reference(CLASS_REFERENCES[class_name], "class_reference")
        with st.form("character_interview_identity"):
            left, right = st.columns(2)
            name = left.text_input("Character name", value=draft.get("name", ""))
            kind = left.selectbox("Character type", [item.value for item in CharacterKind])
            player_id = left.selectbox(
                "Player",
                [None, *[player.id for player in players]],
                format_func=lambda value: (
                    "Unassigned"
                    if value is None
                    else next(player.name for player in players if player.id == value)
                ),
            )
            level = right.number_input("Starting level", 1, 20, draft.get("level", 1))
            background = st.text_input("Background", value=draft.get("background", ""))
            concept = st.text_area(
                "Concept and motivations",
                value=draft.get("concept", ""),
                placeholder="What does this character want, fear, or protect?",
            )
            if st.form_submit_button("Continue to ability scores", type="primary"):
                if not name.strip() or not ancestry.strip() or not class_name.strip():
                    st.error("Name, ancestry, and class or role are required.")
                else:
                    draft.update(
                        name=name.strip(),
                        kind=kind,
                        player_id=player_id,
                        ancestry=ancestry.strip(),
                        class_name=class_name.strip(),
                        level=level,
                        background=background.strip(),
                        alignment=alignment.strip(),
                        concept=concept.strip(),
                    )
                    st.session_state[step_key] = 2
                    st.rerun()
    elif step == 2:
        st.markdown("#### 2 · Ability scores")
        st.write(
            "Enter the final assigned scores. The engine will derive modifiers and save bonuses."
        )
        methods = [
            "Dice roll (4d6, drop lowest)",
            "Standard array",
            "Point buy final scores",
            "Manual entry",
        ]
        method = st.selectbox(
            "Generation method",
            methods,
            index=methods.index(draft.get("ability_method", methods[0])),
            key=f"interview_ability_method_{campaign.id}",
        )
        st.caption("Scores stay hidden while the dice roll, then land one at a time.")
        if st.button("🎲 Roll ability scores", key=f"roll_abilities_{campaign.id}"):
            draft["ability_values"] = animate_ability_scores(method)
            draft["ability_method"] = method
            for ability_name, score in draft["ability_values"].items():
                st.session_state[f"interview_{ability_name}"] = score
            st.rerun()
        with st.form("character_interview_abilities"):
            defaults = [15, 14, 13, 12, 10, 8]
            stored_scores = draft.get("ability_values", {})
            minimum_score = 8 if method == "Point buy final scores" else 1
            maximum_score = 15 if method == "Point buy final scores" else 20
            ability_values = {
                ability_name: st.number_input(
                    ability_name,
                    minimum_score,
                    maximum_score,
                    min(
                        maximum_score,
                        max(
                            minimum_score,
                            stored_scores.get(ability_name, defaults[index]),
                        ),
                    ),
                    key=f"interview_{ability_name}",
                )
                for index, ability_name in enumerate(ABILITY_NAMES)
            }
            if method == "Point buy final scores":
                spent_points = domain_point_buy_total(ability_values)
                st.caption(
                    f"Point buy: {spent_points}/{POINT_BUY_BUDGET} points spent. "
                    "Scores must use the full 27-point budget."
                )
            else:
                st.caption(f"Method recorded for provenance: {method}.")
            back, forward = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 1
                st.rerun()
            if forward.form_submit_button("Continue to combat details", type="primary"):
                if (
                    method == "Point buy final scores"
                    and domain_point_buy_total(ability_values) != POINT_BUY_BUDGET
                ):
                    st.error("Point buy must spend exactly 27 points before continuing.")
                else:
                    draft.update(ability_values=ability_values, ability_method=method)
                    st.session_state[step_key] = 3
                    st.rerun()
    elif step == 3:
        st.markdown("#### 3 · Combat and rules state")
        st.write("These values become the compact combat-facing part of the character sheet.")
        render_rule_reference(COMBAT_RULES_REFERENCE, "combat_rules_reference")
        ability_values = draft.get("ability_values", {})
        level = draft.get("level", 1)
        class_name = draft.get("class_name", "Fighter")
        ancestry = draft.get("ancestry", "Human")
        derived = derive_values(ability_values, class_name, ancestry, level)
        derived_base_ac = derived.armor_class
        derived_max_hp = derived.max_hp
        derived_proficiency = derived.proficiency_bonus
        derived_passive_perception = derived.passive_perception
        derived_hit_die = derived.hit_dice
        derived_spellcasting = derived.spellcasting_ability
        with st.form("character_interview_combat"):
            left, middle, right = st.columns(3)
            armor_class = left.number_input(
                "Armor class (current)",
                0,
                40,
                draft.get("armor_class", derived_base_ac),
            )
            left.caption(
                "Base calculation: 10 + Dexterity modifier; armor and features can change it."
            )
            left.metric("Maximum hit points", derived_max_hp)
            left.caption(f"Level 1 default: {derived_hit_die} maximum + Constitution modifier.")
            max_hp = derived_max_hp
            speed = middle.number_input("Speed (feet)", 0, 200, draft.get("speed", 30))
            middle.metric("Proficiency bonus", derived_proficiency)
            middle.caption("Derived from level; +2 at levels 1–4.")
            right.metric("Passive perception (base)", derived_passive_perception)
            passive_perception = derived_passive_perception
            right.metric("Hit die", derived_hit_die)
            right.metric("Spellcasting ability", derived_spellcasting or "None")
            proficiency = derived_proficiency
            hit_dice = derived_hit_die
            spellcasting = derived_spellcasting
            back, forward = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 2
                st.rerun()
            if forward.form_submit_button("Continue to story and features", type="primary"):
                draft.update(
                    armor_class=armor_class,
                    max_hp=max_hp,
                    speed=speed,
                    proficiency_bonus=proficiency,
                    passive_perception=passive_perception,
                    hit_dice=hit_dice.strip(),
                    spellcasting_ability=spellcasting.strip(),
                )
                st.session_state[step_key] = 4
                st.rerun()
    else:
        st.markdown("#### 4 · Story and features")
        st.write("Finish with the information that makes the sheet playable at the table.")
        lock_identity_key = f"lock_identity_{campaign.id}"
        lock_abilities_key = f"lock_abilities_{campaign.id}"
        lock_identity = st.checkbox(
            "🔒 Lock identity (name, ancestry, class, background, concept)",
            value=st.session_state.get(lock_identity_key, False),
            key=lock_identity_key,
        )
        lock_abilities = st.checkbox(
            "🔒 Lock ability scores",
            value=st.session_state.get(lock_abilities_key, False),
            key=lock_abilities_key,
        )
        if st.button("🎲 Regenerate", key=f"regenerate_character_{campaign.id}"):
            draft.update(
                _regenerate_draft(existing_names, players, draft, lock_identity, lock_abilities)
            )
            st.rerun()
        _render_preview_card(draft)
        with st.form("character_interview_story"):
            notes = st.text_area("Character notes", value=draft.get("notes", ""))
            feature_lines = st.text_area(
                "Features and proficiencies",
                value=draft.get("feature_lines", ""),
                placeholder=(
                    "Second Wind | Recover during a fight\n"
                    "Arcane Recovery | Restore magical resources"
                ),
            )
            back, finish = st.columns(2)
            if back.form_submit_button("Back"):
                st.session_state[step_key] = 3
                st.rerun()
            if finish.form_submit_button("Finish character", type="primary"):
                ability_values = draft.get("ability_values", {})
                class_name = draft.get("class_name", "Fighter")
                ancestry = draft.get("ancestry", "Human")
                derived = derive_values(ability_values, class_name, ancestry, draft.get("level", 1))
                character_draft = CharacterDraft(
                    name=draft["name"],
                    kind=draft["kind"],
                    player_id=draft.get("player_id"),
                    ancestry=ancestry,
                    class_name=class_name,
                    level=draft.get("level", 1),
                    background=draft.get("background", ""),
                    alignment=draft.get("alignment", ""),
                    concept=draft.get("concept", ""),
                    ability_method=_METHOD_LABELS.get(
                        draft.get("ability_method", ""), AbilityScoreMethod.MANUAL
                    ),
                    ability_scores=ability_values,
                    derived=derived,
                    feature_lines=[
                        line.strip() for line in feature_lines.splitlines() if line.strip()
                    ],
                    notes=notes.strip(),
                )
                errors = validate_draft(character_draft)
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    character = character_repository.create_from_draft(
                        session, campaign.id, character_draft
                    )
                    session.commit()
                    st.session_state.pop(draft_key, None)
                    st.session_state.pop(step_key, None)
                    st.success(f"{character.name} is ready for the table.")
                    st.rerun()


def render_character_sheet(character: Character) -> None:
    st.markdown("#### Character sheet")
    identity = st.columns(4)
    identity[0].metric("Class / role", character.class_name or "Unset")
    identity[1].metric("Level", character.level)
    identity[2].metric("Armor class", character.armor_class)
    identity[3].metric("Hit points", f"{character.current_hp}/{character.max_hp}")
    st.markdown("##### Ability scores")
    ability_columns = st.columns(6)
    abilities = {ability.ability_name: ability for ability in character.abilities}
    for column, ability_name in zip(
        ability_columns,
        ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
        strict=True,
    ):
        ability = abilities.get(ability_name)
        column.metric(
            ability_name[:3].upper(),
            ability.score if ability else "—",
            f"{ability.modifier:+d}" if ability else "",
        )
    sheet = character.sheet
    rules = st.columns(5)
    rules[0].metric("Speed", sheet.speed if sheet else "—")
    rules[1].metric("Prof.", sheet.proficiency_bonus if sheet else "—")
    rules[2].metric("Passive", sheet.passive_perception if sheet else "—")
    rules[3].metric("Hit dice", sheet.hit_dice if sheet else "—")
    rules[4].metric("Spellcasting", sheet.spellcasting_ability or "—" if sheet else "—")
    if character.features:
        st.markdown("##### Features and proficiencies")
        st.dataframe(
            [
                {
                    "Feature": feature.name,
                    "Category": feature.category,
                    "Reminder": feature.description,
                }
                for feature in character.features
            ],
            use_container_width=True,
            hide_index=True,
        )


def party_page(session: Session, campaign: Campaign) -> None:
    st.subheader("Party & cast")
    players = character_repository.list_players_for_campaign(session, campaign.id)
    characters = character_repository.list_for_campaign(session, campaign.id)
    with st.expander("New Character", expanded=not characters):
        new_character_interview(session, campaign, players)
    st.dataframe(
        [
            {
                "Name": item.name,
                "Type": item.kind,
                "Player": item.player.name if item.player else "",
                "Species": item.ancestry,
                "Class / role": item.class_name,
                "Level": item.level,
                "AC": item.armor_class,
                "HP": f"{item.current_hp}/{item.max_hp}",
            }
            for item in characters
        ],
        use_container_width=True,
        hide_index=True,
    )
    if characters:
        selected_id = st.selectbox(
            "Open character workspace",
            [character.id for character in characters],
            format_func=lambda character_id: next(
                f"{character.name} · {character.kind}"
                for character in characters
                if character.id == character_id
            ),
            key=f"selected_character_{campaign.id}",
        )
        selected = character_repository.get_workspace(session, selected_id)
        if selected is not None:
            character_workspace(session, campaign, selected)


def render(session: Session, campaign: Campaign) -> None:
    party_page(session, campaign)
