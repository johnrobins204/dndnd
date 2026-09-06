# DNDND Refactor Plan

## Goal

Reduce the 1,900-line Streamlit monolith into small page modules, domain services, repositories, and an explicit intelligence layer while preserving behavior at every step.

## Target Structure

```text
src/dndnd/
├── app.py
├── ui/
│   ├── theme.py
│   ├── navigation.py
│   ├── campaign.py
│   ├── components.py
│   └── pages/
│       ├── briefing.py
│       ├── table.py
│       ├── party.py
│       ├── world.py
│       ├── quests.py
│       ├── journal.py
│       ├── combat.py
│       └── writer.py
├── domain/
│   ├── characters.py
│   ├── quests.py
│   ├── worlds.py
│   └── sessions.py
├── data/
│   ├── repositories/
│   │   ├── campaigns.py
│   │   ├── characters.py
│   │   ├── quests.py
│   │   ├── worlds.py
│   │   └── sessions.py
│   └── database.py
├── intelligence/
│   ├── client.py
│   ├── prompts.py
│   ├── world_guide.py
│   ├── quest_guide.py
│   └── writer.py
├── models.py
├── schemas.py
├── rules.py
└── config.py
```

## Dependency Rules

- `ui/pages` may call domain services and repositories, but should not build raw SQL.
- `domain` must not import Streamlit.
- `data` owns SQLAlchemy queries and transaction-oriented persistence.
- `intelligence` accepts plain domain data and returns draft suggestions; it never writes canonical records.
- `app.py` owns bootstrap, session scope, navigation dispatch, and page registration only.
- Shared rendering belongs in `ui/components.py`, not duplicated across pages.

## Progress

- Shared UI foundation: complete.
- Briefing, The Table, Journal, Combat, and Writer page modules: extracted and active.
- Party, World, and Quests page modules: next extraction batch.
- Data package and initial campaign, character, and session repositories: started.
- World draft/profile persistence is now actively repository-backed.
- QuestRepository is now available for builder migration.
- Character point-buy and proficiency calculations now call the domain module.
- Ollama transport now lives behind the real `intelligence.client` boundary.
- Active routing uses extracted page modules for every sidebar workspace.
- Legacy Party/World/Quests implementations remain in `app.py` as compatibility code;
	deleting them is the final cleanup pass after their nested helpers are moved.
- Removed obsolete Table, Journal, campaign selector, navigation, and briefing implementations
  from `app.py`; their extracted modules are the active routes.
- Domain package for character, world, quest, and session logic: started.
- Intelligence package for client, prompts, world guide, quest guide, and writer boundaries: started.

## Sequential Extraction Plan

### Phase 1: Shared UI Foundation

- Extract theme CSS and visual primitives to `ui/theme.py`.
- Extract sidebar workspace navigation to `ui/navigation.py`.
- Extract campaign selection/creation to `ui/campaign.py`.
- Extract briefing dashboard to `ui/pages/briefing.py`.
- Keep compatibility wrappers in `app.py` temporarily if needed.
- Validate browser output and all checks.

### Phase 2: Page Extraction

Extract each page as a `render(session, campaign)` function:

1. Table
2. Journal
3. Combat
4. Writer
5. Party
6. Quests
7. World

Move page-local helper functions with their owning page. Keep cross-page helpers in shared UI or domain modules.

### Phase 3: Domain Services

Move behavior out of UI:

- Character creation, randomization, ability generation, point buy, and derived rules values.
- World draft persistence, readiness checks, canonical acceptance, and exports.
- Quest draft construction and canonical acceptance.
- Session lifecycle and transcript commands.

Services should accept typed values and return typed results.

### Phase 4: Data Repositories

Introduce repositories around repeated SQLAlchemy access:

- Campaigns
- Characters
- Worlds and drafts
- Quests
- Sessions

Use explicit eager loading for page detail views to prevent detached-instance errors.

### Phase 5: Intelligence Layer

Move Ollama transport behind a protocol and separate prompt/guide services:

- `intelligence/client.py`: transport only.
- `intelligence/prompts.py`: prompt construction.
- `intelligence/world_guide.py`: bounded world guidance.
- `intelligence/quest_guide.py`: bounded quest guidance.
- `intelligence/writer.py`: session script generation.

All generated results remain draft content until explicit acceptance.

### Phase 6: Cleanup

- Remove compatibility wrappers from `app.py`.
- Add package `__init__.py` files.
- Update README architecture and development commands.
- Add tests for repository/service boundaries.
- Run full Ruff, mypy, pytest, and live Streamlit verification.

## Working Rules

- Make one extraction slice at a time.
- Preserve public behavior before improving behavior.
- Run focused tests immediately after each slice.
- Never combine unrelated UI redesign with structural extraction.
- Keep user-created data and existing SQLite tables intact.
