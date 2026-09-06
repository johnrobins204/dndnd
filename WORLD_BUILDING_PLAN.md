# DNDND World-Building Plan

## Purpose

Build a guided world-building experience for a solo Dungeon Master. The experience should help a user create a playable world or add structured material to an existing world without requiring them to know world-building terminology or complete an intimidating blank page.

The creation flow must be deterministic. Intelligence may clarify, expand, connect, and challenge user input, but it must not change the canonical question order or silently write generated material into the world.

## Design Principles

### Cognitive Load

- Ask one coherent question group at a time.
- Keep each step focused on one decision or one related cluster of decisions.
- Use concrete prompts instead of large empty text areas.
- Keep advanced details behind progressive disclosure.
- Show a short summary after each major section.
- Preserve drafts between steps and reruns.

### User Agency

- Every generated suggestion is a draft until accepted.
- Always offer `I am not sure yet` where uncertainty is legitimate.
- Always allow freeform input alongside structured options.
- Never silently resolve contradictions.
- Let the user accept, edit, reject, or defer suggestions.

### Narrative Elicitation

Ask about the world as a lived place rather than only as an encyclopedia:

- What does this world value?
- What does it fear?
- What does it remember incorrectly?
- What does ordinary life feel like?
- What changes if nobody intervenes?

Use goals, fears, tensions, costs, and tradeoffs to produce playable material.

### Inclusive Question Design

- Use plain language.
- Define unfamiliar terms inline.
- Provide examples without implying a correct answer.
- Support `I do not know`, `not relevant`, and `leave this mysterious`.
- Keep help text brief and action-focused.
- Do not require a user to write long prose to continue.

## Research Basis

The interaction model is based on:

- [GOV.UK: Designing good questions](https://www.gov.uk/service-manual/design/designing-good-questions)
  - Use closed questions where appropriate.
  - Ask only questions with a known purpose.
  - Explain consequences and provide concise help.
  - Give users an `I am not sure` path where valid.
- [GOV.UK: Structuring forms](https://www.gov.uk/service-manual/design/form-structure)
  - Maintain a question protocol.
  - Start with one coherent task per step.
  - Use branching only when it reduces irrelevant questions.
  - Save answers as users progress.
- [GOV.UK: Making services more inclusive](https://www.gov.uk/service-manual/design/making-your-service-more-inclusive)
  - Design for time, confidence, comprehension, device, and emotional barriers.
  - Avoid assuming expertise or stable attention.
- [Nielsen Norman Group: Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
  - Show important information first.
  - Defer advanced details.
  - Make progression obvious.
  - Avoid excessive disclosure levels.
- [Official D&D 2024 rules](https://www.dndbeyond.com/sources/dnd/br-2024/playing-the-game)
  - Use the ruleset as a reference for world-facing terms, playability, and campaign context.

## Fixed World-Creation Path

The create flow uses eight fixed steps. The order is intentional and should not be changed by the intelligence layer.

### Step 1: World Premise

Question: `What is this world about?`

Capture:

- World name
- One-sentence premise
- Campaign mood
- What makes the world distinct

Mood options:

- Heroic
- Grim
- Mysterious
- Whimsical
- Political
- Mythic
- Horror
- Exploration-focused

Support:

- `I am not sure yet`
- `Give me three starting ideas`

Canonical output: `WorldProfile.premise`, `WorldProfile.mood`, `WorldProfile.distinction`.

### Step 2: Scope And Focus

Question: `What part of the world matters first?`

Scope options:

- One settlement
- One region
- One continent
- Several connected nations
- A whole planet
- A planar or multi-world setting

Follow-up: `Where should the first campaign begin?`

Capture:

- World scope
- Starting region
- Detail priority
- Areas intentionally left unknown

The user should be able to start small. The system should not pressure them to design a whole planet before creating a playable location.

### Step 3: Physical Shape

Question: `What does the world feel like to travel through?`

Capture:

- Major landforms
- Climate
- Oceans and waterways
- Natural barriers
- Strange or magical geography
- Travel difficulty

Prompt cards:

- Where is travel easy?
- Where is travel dangerous?
- What natural feature defines the region?
- What place should not exist, but does?

The intelligence layer may suggest consequences, but suggestions must be marked as suggestions.

### Step 4: History And Change

Question: `What happened that still affects the present?`

Capture three events:

1. Origin: how the current age began.
2. Turning point: the event that permanently changed the world.
3. Recent event: something within living memory.

For each event:

- What happened?
- Who benefited?
- Who suffered?
- What remains unresolved?
- What false version do people believe?

Canonical output: `WorldHistoryEvent` records with public truth, secrets, rumors, and unresolved consequences.

### Step 5: Power And Society

Question: `Who has power, and what do they want?`

Repeated faction mini-interview:

- Faction name
- Public purpose
- Actual objective
- Resource or advantage
- Rival
- Internal tension
- What happens if it succeeds?
- What happens if it fails?

Power categories:

- Government
- Religion
- Trade
- Military
- Arcane
- Criminal
- Cultural
- Natural or supernatural

The user can add another faction, continue with a minimal world, or request suggestions for a counter-faction.

### Step 6: Everyday Life

Question: `What is ordinary life like here?`

Capture:

- Common food
- Work and trade
- Family and community patterns
- Education
- Justice
- Religion or ritual
- Common fears
- Celebrations
- What outsiders misunderstand

Concrete prompts:

- What would a child know?
- What would travelers complain about?
- What would people risk punishment to obtain?
- What does a normal evening look like?

### Step 7: The Fantastic And The Forbidden

Question: `What is possible here that is impossible elsewhere?`

Capture:

- Magic source
- Who can access it
- Cost
- Limitation
- Forbidden practices
- Public misunderstanding
- Real supernatural threat
- False supernatural rumor

Use the structure:

- Capability
- Cost
- Limitation
- Social consequence
- Visible sign

The intelligence layer should challenge unconstrained magic by asking what it costs or prevents.

### Step 8: Playable Starting Situation

Question: `What is happening when the characters arrive?`

Capture:

- Starting location
- Immediate problem
- Visible stakes
- Hidden stakes
- Important NPC
- First meaningful choice
- What changes if players do nothing

Completion review should show:

- Premise
- Starting region
- Current conflict
- Major factions
- Three locations
- Three NPC seeds
- One unresolved mystery
- One immediate adventure hook

The world should not be marked complete until it has at least one playable starting situation.

## Existing-World Add Path

Adding to an existing world is a separate fixed flow and must not repeat world creation.

1. What are you adding?
   - Location
   - Faction
   - Historical event
   - Culture
   - Religion
   - Magic rule
   - NPC group
   - Conflict
   - Adventure hook
2. Where does it belong?
   - Existing region
   - Existing location
   - Existing faction
   - Timeline event
   - New branch
3. What does it change?
   - Who benefits?
   - Who is threatened?
   - What becomes possible?
   - What becomes harder?
4. How visible is it?
   - Public fact
   - Local knowledge
   - Secret
   - Rumor
   - False belief
5. What should the DM get from it?
   - NPC seed
   - Quest hook
   - Location detail
   - Conflict
   - Encounter idea
   - Player-facing description
6. Review and commit.

The review must show proposed additions, affected records, contradictions, and explicit acceptance controls.

## Intelligence Layer Contract

The intelligence layer has four modes:

### Clarify

Ask one targeted follow-up when an answer is too broad.

Example: `You described the kingdom as oppressive. Is that mainly military, economic, religious, or social?`

### Expand

Offer three distinct options with different tones or consequences.

Example: `What defines the frontier?`

- A failed imperial colony
- A wilderness sacred to ancient spirits
- A trade route built over forbidden ruins

### Connect

Point out relationships to existing world facts.

Example: `This faction's control of salt conflicts with the river-trade faction. Should they compete, cooperate, or operate in different regions?`

### Challenge

Identify missing consequences or contradictions without resolving them silently.

Example: `The region is isolated by mountains, but you describe frequent international trade. Which explanation fits?`

Every intelligence suggestion must carry:

- Draft status
- Source: generated
- Confidence: suggested
- Accept / edit / reject controls
- Links to affected entities

## Draft And Canonical State

Add draft state before adding canonical world records.

Proposed models:

- `WorldProfile`
- `WorldRegion`
- `WorldHistoryEvent`
- `WorldFaction`
- `WorldCulture`
- `WorldBelief`
- `WorldMagicRule`
- `WorldQuestionResponse`
- `WorldDraft`
- `WorldDraftChange`
- `WorldRelationship`

Important fields:

- `status`: draft, accepted, rejected
- `visibility`: public, local, secret, rumor, false
- `source`: user, generated, imported
- `confidence`: user-confirmed, suggested, unresolved
- `created_at`
- `accepted_at`
- `notes`

## Streamlit UX Contract

The create flow should match the character creator pattern:

- Progress indicator
- One focused step
- Back and Continue controls
- Draft saved in `st.session_state`
- Draft persisted for interruption recovery
- `I am not sure yet` option
- Brief inline help
- Intelligence suggestions in a secondary panel
- Review before canonical save

Use a living summary rail showing:

- Premise
- Current scope
- Starting region
- Major tension
- Known factions
- Unresolved questions

The summary updates after every completed step.

## Question Protocol

Before adding a question, record:

- The question text
- Why the answer is needed
- Which model field it populates
- Whether it is required or optional
- What uncertainty option exists
- What validation applies
- What downstream suggestions it enables
- Whether the answer is canonical or draft-only

No question should exist solely because it is traditional world-building trivia.

## Implementation Phases

### Phase 1: Deterministic Draft Foundation

- Define question and step schemas.
- Add draft state model.
- Implement fixed eight-step Streamlit flow.
- Add autosave and Back/Continue navigation.
- Add section summaries.

### Phase 2: Canonical World Graph

- Add normalized world models.
- Add accepted-draft commit operations.
- Link regions, locations, factions, events, NPCs, items, and quests.
- Add visibility and source metadata.

### Phase 3: Existing-World Add Flow

- Add the fixed add-to-world questionnaire.
- Add entity linking.
- Add change summaries and contradiction warnings.

### Phase 4: Intelligence Assistance

- Add clarify suggestions.
- Add three-option expansion suggestions.
- Add connection detection.
- Add contradiction challenges.
- Require explicit acceptance for generated material.

### Phase 5: Playability And Review

- Generate a playable starting situation.
- Add world completeness checks.
- Add exportable world brief.
- Add tests for draft acceptance, rejection, visibility, and conflict detection.

## Acceptance Criteria

A first version is ready when:

- A novice can complete world creation without knowing world-building jargon.
- The fixed path always follows the same eight sections.
- The user can pause and resume without losing answers.
- Every accepted world has a premise, scope, starting region, conflict, and playable situation.
- Generated suggestions never become canon without explicit acceptance.
- Existing world additions show their affected entities before saving.
- The user can mark details as unknown, secret, rumor, or unresolved.
- The intelligence layer can enrich the world without controlling the user’s creative direction.
- The flow remains useful with intelligence disabled.
