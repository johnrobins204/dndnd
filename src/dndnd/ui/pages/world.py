"""World page, builder, and canonical acceptance workflows."""

import json

import streamlit as st
from sqlalchemy.orm import Session

from dndnd.config import get_settings
from dndnd.data.repositories.worlds import WorldRepository
from dndnd.intelligence.client import OllamaClient, OllamaError
from dndnd.models import (
    Campaign,
    Location,
    WorldDraftChange,
    WorldFaction,
    WorldHistoryEvent,
    WorldMagicRule,
    WorldProfile,
    WorldStartingSituation,
)
from dndnd.prompting import WORLD_GUIDANCE_MODES, build_world_guidance_prompt
from dndnd.world_checks import check_world_draft
from dndnd.world_export import build_world_brief
from dndnd.world_questions import (
    WORLD_QUESTIONS,
    WorldResponseType,
    WorldStep,
    questions_for_step,
    world_step_order,
)

world_repository = WorldRepository()


def render(session: Session, campaign: Campaign) -> None:
    st.subheader("World")
    with st.expander("Build or expand the world", expanded=True):
        world_builder(session, campaign)
    with st.expander("Add to existing world"):
        world_add_flow(session, campaign)
    with st.expander("Locations"):
        with st.form("add_location", clear_on_submit=True):
            name = st.text_input("Location")
            environment = st.text_input(
                "Environment", placeholder="Urban, forest, dungeon…"
            )
            description = st.text_area("What players can observe")
            secrets = st.text_area("DM-only secrets")
            if st.form_submit_button("Add location", type="primary") and name.strip():
                session.add(
                    Location(
                        campaign_id=campaign.id,
                        name=name.strip(),
                        environment=environment,
                        description=description,
                        secrets=secrets,
                    )
                )
                session.commit()
                st.rerun()
        for location in world_repository.list_locations_for_campaign(
            session, campaign.id
        ):
            with st.expander(
                f"{location.name} · {location.environment or 'Unclassified'}"
            ):
                st.write(location.description or "No public description yet.")
                if location.secrets:
                    st.warning(f"DM secret: {location.secrets}")


def world_add_flow(session: Session, campaign: Campaign) -> None:
    st.markdown("#### Add to the world")
    st.caption("Create a reviewable contribution without changing canon immediately.")
    with st.form(f"world_add_{campaign.id}", clear_on_submit=True):
        change_type = st.selectbox(
            "What are you adding?",
            [
                "Location",
                "Faction",
                "Historical event",
                "Culture",
                "Religion",
                "Magic rule",
                "NPC group",
                "Conflict",
                "Adventure hook",
            ],
        )
        title = st.text_input("Name or short title")
        placement = st.text_input(
            "Where does it belong?",
            placeholder="Existing region, settlement, faction, timeline, or new branch",
        )
        details = st.text_area("What is it?")
        consequences = st.text_area(
            "What does it change? Who benefits or is threatened?"
        )
        visibility = st.selectbox(
            "How visible is it?",
            ["Public fact", "Local knowledge", "Secret", "Rumor", "False belief"],
        )
        intended_output = st.selectbox(
            "What should the DM get from it?",
            [
                "NPC seed",
                "Quest hook",
                "Location detail",
                "Conflict",
                "Encounter idea",
                "Player-facing description",
            ],
        )
        if st.form_submit_button("Save as draft change", type="primary"):
            if not title.strip() or not details.strip():
                st.error("Add a title and details before saving the draft.")
            else:
                session.add(
                    WorldDraftChange(
                        campaign_id=campaign.id,
                        change_type=change_type,
                        title=title.strip(),
                        placement=placement.strip(),
                        details=details.strip(),
                        consequences=consequences.strip(),
                        visibility=visibility,
                        intended_output=intended_output,
                    )
                )
                session.commit()
                st.rerun()
    drafts = world_repository.list_draft_changes_for_campaign(session, campaign.id)
    if drafts:
        st.markdown("#### Pending world changes")
        for change in drafts:
            with st.expander(
                f"{change.title} · {change.change_type} · {change.status}"
            ):
                st.caption(f"{change.visibility} · {change.intended_output}")
                st.write(change.details)
                if change.placement:
                    st.write(f"**Placement:** {change.placement}")
                if change.consequences:
                    st.write(f"**Consequences:** {change.consequences}")


def world_builder(session: Session, campaign: Campaign) -> None:
    draft_key = f"world_draft_{campaign.id}"
    step_key = f"world_step_{campaign.id}"
    persisted_draft = world_repository.get_draft(session, campaign.id)
    if draft_key not in st.session_state:
        st.session_state[draft_key] = (
            json.loads(persisted_draft.answers_json) if persisted_draft else {}
        )
    if step_key not in st.session_state and persisted_draft:
        st.session_state[step_key] = persisted_draft.current_step
    if persisted_draft and persisted_draft.is_reviewing:
        st.session_state[f"world_review_{campaign.id}"] = True
    persisted_answers = (
        json.loads(persisted_draft.answers_json) if persisted_draft else {}
    )
    if persisted_answers.get("_review_opened"):
        st.session_state[f"world_review_opened_{campaign.id}"] = True
    draft: dict[str, str] = st.session_state[draft_key]
    steps = world_step_order()
    step_index = int(st.session_state.get(step_key, 0))
    step_index = max(0, min(step_index, len(steps) - 1))
    current_step = steps[step_index]
    step_questions = questions_for_step(current_step)

    st.markdown("### World builder")
    st.caption("A focused path from premise to a playable starting situation.")
    st.progress(
        (step_index + 1) / len(steps),
        text=f"Step {step_index + 1} of {len(steps)} · {current_step.replace('_', ' ').title()}",
    )

    summary, questions = st.columns([1, 2])
    with summary:
        st.markdown("#### World taking shape")
        completed = 0
        for question in WORLD_QUESTIONS:
            value = draft.get(question.key, "")
            if value and value != question.uncertainty_option:
                completed += 1
        st.metric("Answered", f"{completed}/{len(WORLD_QUESTIONS)}")
        for key, label in (
            ("world_name", "Name"),
            ("premise", "Premise"),
            ("scope", "Scope"),
            ("starting_region", "Starting region"),
            ("starting_problem", "Current problem"),
        ):
            summary_value = draft.get(key)
            if summary_value:
                st.markdown(f"**{label}**  \n{summary_value[:120]}")
            else:
                st.caption(f"{label} · not set")
    with questions:
        st.markdown(f"#### {current_step.replace('_', ' ').title()}")
        st.write(
            "Answer what you know. You can leave uncertainty visible and return later."
        )
        with st.form(f"world_step_{campaign.id}_{current_step}"):
            responses: dict[str, str] = {}
            for question in step_questions:
                st.markdown(f"**{question.prompt}**")
                if question.help_text:
                    st.caption(question.help_text)
                options = (question.uncertainty_option, *question.options)
                if question.response_type is WorldResponseType.SINGLE_CHOICE:
                    existing = draft.get(question.key, question.uncertainty_option)
                    responses[question.key] = (
                        st.selectbox(
                            question.key,
                            options,
                            index=options.index(existing) if existing in options else 0,
                            label_visibility="collapsed",
                        )
                        or ""
                    )
                elif question.response_type is WorldResponseType.LONG_TEXT:
                    responses[question.key] = (
                        st.text_area(
                            question.key,
                            value=draft.get(question.key, ""),
                            height=120,
                            placeholder=question.uncertainty_option,
                            label_visibility="collapsed",
                        )
                        or ""
                    )
                else:
                    responses[question.key] = (
                        st.text_input(
                            question.key,
                            value=draft.get(question.key, ""),
                            placeholder=question.uncertainty_option,
                            label_visibility="collapsed",
                        )
                        or ""
                    )
            back, forward = st.columns(2)
            if step_index > 0 and back.form_submit_button("Back"):
                for key, value in responses.items():
                    draft[key] = value.strip()
                st.session_state[step_key] = step_index - 1
                save_world_draft(session, campaign.id, draft, step_index - 1, False)
                st.rerun()
            next_label = "Review world" if step_index == len(steps) - 1 else "Continue"
            if forward.form_submit_button(next_label, type="primary"):
                for key, value in responses.items():
                    draft[key] = value.strip()
                if step_index < len(steps) - 1:
                    st.session_state[step_key] = step_index + 1
                    save_world_draft(session, campaign.id, draft, step_index + 1, False)
                    st.rerun()
                st.session_state[f"world_review_{campaign.id}"] = True
                st.session_state[f"world_review_opened_{campaign.id}"] = True
                save_world_draft(session, campaign.id, draft, step_index, True, True)
                st.rerun()

    if st.session_state.get(f"world_review_{campaign.id}"):
        st.divider()
        st.markdown("<div id='world-review'></div>", unsafe_allow_html=True)
        st.markdown("#### Review before saving")
        if st.session_state.get(f"world_review_opened_{campaign.id}"):
            st.success(
                "Review is open. Your draft is saved locally and ready for acceptance."
            )
        st.info(
            "This is still a draft. Canonical world records are not changed until you accept it."
        )
        for question in WORLD_QUESTIONS:
            value = draft.get(question.key, question.uncertainty_option)
            st.markdown(
                f"**{question.prompt}**  \n{value or question.uncertainty_option}"
            )
        st.markdown("#### Readiness checks")
        checks = check_world_draft(draft)
        for check in checks:
            if check.severity == "missing":
                st.error(check.message)
            elif check.severity in ("challenge", "contradiction"):
                st.warning(check.message)
            else:
                st.success(check.message)
        st.download_button(
            "Download world brief",
            build_world_brief(draft, checks),
            file_name=f"{draft.get('world_name', 'world').replace(' ', '-')}.md",
            mime="text/markdown",
            key=f"download_world_{campaign.id}",
        )
        existing_profile = world_repository.get_profile(session, campaign.id)
        if existing_profile is not None:
            st.success("This campaign already has an accepted world profile.")
        elif not any(check.severity == "missing" for check in checks) and st.button(
            "Accept world as canonical",
            key=f"accept_world_{campaign.id}",
            type="primary",
        ):
            profile = WorldProfile(
                campaign_id=campaign.id,
                name=draft.get("world_name", "Unnamed world"),
                premise=draft.get("premise", ""),
                mood=draft.get("mood", ""),
                scope=draft.get("scope", ""),
                starting_region=draft.get("starting_region", ""),
                geography=draft.get("geography", ""),
                everyday_life=draft.get("everyday_life", ""),
            )
            profile.history_events.append(
                WorldHistoryEvent(
                    title="The turning point",
                    description=draft.get("turning_point", ""),
                )
            )
            profile.factions.append(
                WorldFaction(
                    name="Initial power structure",
                    public_purpose=draft.get("power_holders", ""),
                )
            )
            profile.magic_rules.append(
                WorldMagicRule(
                    name="The world's fantastic rule",
                    capability=draft.get("fantastic_rule", ""),
                )
            )
            profile.starting_situations.append(
                WorldStartingSituation(
                    title="The campaign begins",
                    problem=draft.get("starting_problem", ""),
                )
            )
            session.add(profile)
            session.commit()
            world_repository.delete_draft(session, campaign.id)
            session.commit()
            st.session_state[f"world_accepted_{campaign.id}"] = True
            st.success("World accepted as canonical campaign data.")
            st.rerun()
        if st.button("Start this draft over", key=f"reset_world_{campaign.id}"):
            st.session_state.pop(draft_key, None)
            st.session_state.pop(step_key, None)
            st.session_state.pop(f"world_review_{campaign.id}", None)
            if persisted_draft:
                session.delete(persisted_draft)
                session.commit()
            st.rerun()

    with st.expander("Optional world guide"):
        world_guidance_panel(session, campaign, current_step, draft)


def save_world_draft(
    session: Session,
    campaign_id: int,
    draft: dict[str, str],
    current_step: int,
    is_reviewing: bool,
    review_opened: bool = False,
) -> None:
    world_repository.save_draft(
        session, campaign_id, draft, current_step, is_reviewing, review_opened
    )
    session.commit()


def world_guidance_panel(
    session: Session,
    campaign: Campaign,
    step: WorldStep,
    draft: dict[str, str],
) -> None:
    st.divider()
    st.markdown("#### World guide")
    st.caption(
        "Optional intelligence assistance. Suggestions stay in draft state until you accept "
        "the world review."
    )
    mode = st.selectbox(
        "Guide mode",
        WORLD_GUIDANCE_MODES,
        key=f"world_guide_mode_{campaign.id}_{step.value}",
    )
    if st.button("Ask the guide", key=f"world_guide_{campaign.id}_{step.value}"):
        existing_profile = world_repository.get_profile(session, campaign.id)
        existing_context = (
            f"{existing_profile.name}: {existing_profile.premise}"
            if existing_profile
            else ""
        )
        prompt = build_world_guidance_prompt(
            mode=mode,
            step_name=step.value.replace("_", " ").title(),
            answers=draft,
            existing_world=existing_context,
        )
        try:
            with st.spinner("The guide is considering the next thread..."):
                st.session_state[f"world_guide_result_{campaign.id}"] = OllamaClient(
                    get_settings()
                ).generate(prompt)
        except OllamaError as error:
            st.error(str(error))
    result = st.session_state.get(f"world_guide_result_{campaign.id}")
    if result:
        st.info(result)
        accept, reject = st.columns(2)
        if accept.button("Keep as draft note", key=f"keep_guide_{campaign.id}"):
            notes = draft.get("guidance_notes", "")
            draft["guidance_notes"] = f"{notes}\n{result}".strip()
            st.session_state[f"world_guide_result_{campaign.id}"] = None
            st.success("Suggestion kept in the draft notes.")
        if reject.button("Dismiss suggestion", key=f"dismiss_guide_{campaign.id}"):
            st.session_state[f"world_guide_result_{campaign.id}"] = None
            st.rerun()
