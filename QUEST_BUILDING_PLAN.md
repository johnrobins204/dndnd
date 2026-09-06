# DNDND Quest-Building Plan

## Purpose

Create quests through a fixed, psychology-informed interview that turns a vague idea into a playable situation with agency, stakes, escalation, opposition, chapters, triggers, and consequences.

The fixed path must work without intelligence. The intelligence layer can clarify, expand, connect, and challenge answers, but it must not reorder the path or write canonical quest data without explicit acceptance.

## Elicitation Principles

- Ask one meaningful decision at a time.
- Start with the emotional or practical reason the quest matters.
- Prefer concrete choices and examples over blank-page prompts.
- Ask for player agency explicitly: what can characters choose, refuse, or change?
- Ask for consequences rather than only lore.
- Make uncertainty valid: rumor, unknown, hidden, or not decided yet.
- Show momentum with a live quest summary.
- Save draft answers as the user advances.
- Keep advanced trigger and reward details behind later steps.

## Fixed Creation Path

### Step 1: The Hook

Question: `Why would anyone care about this?`

Capture:

- Quest title
- Initial hook
- Emotional invitation
- Who first presents the problem

The hook should express a situation, not just a task.

### Step 2: The Want

Question: `What does someone want badly enough to act?`

Capture:

- Primary objective
- Who wants it
- Why now
- What happens if they wait

This establishes motivation and urgency.

### Step 3: The Opposition

Question: `Who or what makes this difficult?`

Capture:

- Opposing NPC, faction, force, or environment
- Opposition goal
- Opposition resource
- What the opposition believes it is protecting

Avoid making opposition evil by default. Conflicting goals create better choices.

### Step 4: The Choice

Question: `What meaningful choice should the party face?`

Capture:

- Choice A
- Choice B
- What each choice protects
- What each choice sacrifices
- Whether a third path is possible

A quest should not be a single correct answer disguised as an adventure.

### Step 5: Escalation

Question: `What changes if the party delays or fails?`

Capture:

- Immediate consequence
- Escalated consequence
- Who benefits from delay
- What new danger appears

This produces a living situation rather than a static checklist.

### Step 6: Chapters And Triggers

Question: `What are the next three playable beats?`

Capture:

- Chapter 1: discovery or commitment
- Chapter 2: complication or reversal
- Chapter 3: confrontation or transformation
- Trigger that opens each chapter
- Objective for each chapter

Keep chapters playable and observable. Avoid requiring a complete novel outline.

### Step 7: Rewards And Meaning

Question: `What changes for the characters when this is resolved?`

Capture:

- Material reward
- Relationship or faction consequence
- Information gained
- New opportunity
- Cost of success
- What remains unresolved

Rewards should reinforce the quest’s meaning, not only provide currency or experience.

### Step 8: Table-Ready Opening

Question: `What can the DM put in front of the players first?`

Capture:

- Opening location
- Opening image or sensory detail
- NPC present
- Immediate actionable problem
- First choice available
- Hidden DM information

The quest is ready when the DM can begin play without inventing a missing opening scene.

## Existing-Quest Add Path

For an existing quest, use a shorter fixed path:

1. What are you adding?
   - Chapter
   - Objective
   - Trigger
   - NPC
   - Location
   - Item
   - Reward
   - Complication
2. Where does it attach?
3. What changes because of it?
4. Who knows about it?
5. Is it canonical, draft, rumor, or secret?
6. Review and accept.

## Intelligence Contract

The guide has four bounded modes:

- **Clarify:** ask one targeted question about motivation, stakes, or agency.
- **Expand:** offer three different quest directions.
- **Connect:** relate the quest to existing characters, factions, locations, or items.
- **Challenge:** identify a missing choice, weak consequence, or contradiction.

Every suggestion must be labelled draft/generated and must offer accept, edit, or dismiss. The guide cannot silently create objectives, triggers, or canonical lore.

## Draft And Canonical State

Draft creation should eventually produce:

- Quest blueprint
- Chapters
- Objectives
- Triggers
- Rewards
- NPC and item links
- Opening scene

Canonical acceptance should be explicit and should show:

- What will be created
- What existing records are linked
- Any contradictions
- Any unresolved fields

## UX Contract

- Eight fixed steps
- Progress indicator
- Back and Continue
- SQLite-backed draft recovery
- Live quest summary rail
- Optional help text
- Review-before-save
- Minimal vertical stacking: current step first, review second, optional guide and existing quest tools collapsed

## Acceptance Criteria

- A new DM can create a playable quest without knowing adventure-design jargon.
- Every quest has a hook, motivation, opposition, meaningful choice, escalation, and opening scene.
- The flow works with intelligence disabled.
- The intelligence layer cannot change the fixed path.
- Generated suggestions never become canonical without explicit acceptance.
- The result can be represented by the existing Quest, QuestChapter, QuestObjective, QuestTrigger, QuestReward, QuestCharacter, and QuestItem models.
