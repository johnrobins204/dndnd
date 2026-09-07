# Character Randomizer Sprint Plan

## Goal

Polish the DNDND level-1 character randomizer so that one-click and guided generation produces valid D&D 5e (2024) characters with class-aware ability scores, ancestry/background bonuses, correct derived statistics, collision-free names, and a preview-before-save UX — while moving all business rules out of the UI layer and into `src/dndnd/domain/characters.py`.

## Constraints and standards

- Target Python 3.12, use `uv` for dependency and test runs.
- Stay local-first: no rules or character data leaves the machine except to the configured Ollama endpoint.
- Follow the layer boundaries in [AGENTS.md](../AGENTS.md) and [ADR 001](../docs/adr/001-established-patterns-and-starting-architecture.md):
  - UI lives in `src/dndnd/ui/`.
  - Business rules live in `src/dndnd/domain/`.
  - Persistence helpers live in `src/dndnd/data/repositories/`.
  - Static reference tables live in `src/dndnd/rules.py`.
- Every sprint must leave `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` passing.
- Each sprint is a focused, reviewable slice (roughly 1–5 files and 100–300 LOC).
- Level 1 only; equipment, feats, spells, subclasses, multi-classing, and level-up are out of scope.
- From Sprint 1 through Sprint 7, any change to a rule table must be mirrored in both `src/dndnd/rules.py` and the old inline tables in `src/dndnd/ui/pages/party.py`. The old inline tables must be removed entirely in Sprint 8 with no surviving references.
- Every sprint that adds domain behavior must include at least one deterministic test before it is considered complete, even if broader test migration remains in Sprint 7.

## Assumptions and decisions

- Background ability bonuses use a fixed +2/+1 pair per background table (no user choice at generation time).
- Ability-score provenance persists as the method name on `CharacterSheet`; raw pre-bonus scores are not persisted separately.
- Name uniqueness is checked with an in-memory set during generation and a repository helper during validation.
- Randomness is always injected as `random.Random` so tests can seed it deterministically.

## Affected areas and key files

- `src/dndnd/domain/characters.py` — new home for generation, derivation, and validation logic.
- `src/dndnd/rules.py` — static tables for classes, ancestries, backgrounds, hit dice, spellcasting, and starting features.
- `src/dndnd/ui/pages/party.py` — UI stripped of business rules; wired to domain functions.
- `src/dndnd/app.py` — remove re-exports of character-generation helpers.
- `src/dndnd/data/repositories/characters.py` — add name-existence check and `create_from_draft`.
- `src/dndnd/models.py` and `src/dndnd/db.py` — add `ability_score_method` provenance column and SQLite migration.
- `tests/test_random_character.py` — migrated to import from the domain and expanded with deterministic tests.

## Sprint 1 — Domain model and static rules tables

### Objective
Establish the domain dataclasses and move the static rules tables from `party.py` into `rules.py` so later sprints have a shared vocabulary.

### Inputs
- `docs/adr/002-character-randomizer-architecture.md`
- Existing inline tables in `src/dndnd/ui/pages/party.py`

### Outputs
- `AbilityScoreMethod` enum in `src/dndnd/domain/characters.py`.
- `CharacterDraft` and `DerivedValues` dataclasses in `src/dndnd/domain/characters.py`.
- New static tables in `src/dndnd/rules.py`:
  - `CLASS_PRIORITIES`
  - `ANCESTRY_TRAITS` (speed and ability bonuses)
  - `BACKGROUND_BONUSES`
  - `HIT_DICE`
  - `HIT_DIE_SIZES`
  - `SPELLCASTING_ABILITIES`
  - `STARTING_FEATURES`
  - `BACKGROUND_OPTIONS`
  - `RANDOM_CONCEPTS`

### Files likely to change
- `src/dndnd/domain/characters.py`
- `src/dndnd/rules.py`

### Acceptance criteria
- `CharacterDraft` exposes identity fields, ability method, scores, derived values, feature lines, and notes.
- `AbilityScoreMethod` covers standard array, 4d6-drop-lowest, point buy, and manual entry with values that match the current UI labels.
- Every `CharacterClass` value has a class-priority list and a hit die.
- Every `CharacterAncestry` value has ancestry traits.
- The 17 background options have a +2/+1 pair and suggested proficiencies.
- No executable logic is added beyond dataclass and table definitions.

### Validation steps
- `uv run ruff check .`
- `uv run mypy src`
- `uv run pytest` (existing suite must still pass)

### Dependencies
- None.

## Sprint 2 — Ability-score generation and class-aware assignment

### Objective
Implement the pure functions that produce ability scores for each generation method and place them according to class priorities.

### Inputs
- `AbilityScoreMethod` and `CLASS_PRIORITIES` from Sprint 1.

### Outputs
- `generate_ability_scores(method: AbilityScoreMethod, rng: random.Random) -> dict[str, int]`
- `assign_scores_by_class(scores: list[int], class_name: str) -> dict[str, int]`
- `ability_modifier(score: int) -> int`
- `ABILITY_NAMES` constant

### Files likely to change
- `src/dndnd/domain/characters.py`
- `tests/test_random_character.py`

### Acceptance criteria
- Standard array returns exactly the values `[15, 14, 13, 12, 10, 8]`.
- 4d6-drop-lowest returns scores between 3 and 18.
- Point buy returns scores between 8 and 15 with a total cost of 27.
- Manual entry raises a clear error or returns an empty placeholder (UI owns manual input).
- Class assignment puts the highest score in the class primary ability, the next highest in the secondary/weapon ability, then Constitution if unassigned, then fills the rest in a sensible order.
- All functions use the injected `random.Random` instance.

### Validation steps
- New deterministic tests using `random.Random(seed)`.
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1.

## Sprint 3 — Ancestry and background bonuses

### Objective
Apply 2024-style ancestry and background bonuses and enforce the 20 ability-score cap.

### Inputs
- `ANCESTRY_TRAITS` and `BACKGROUND_BONUSES` from Sprint 1.
- Assigned scores from Sprint 2.

### Outputs
- `apply_ancestry_bonuses(scores: dict[str, int], ancestry: str) -> dict[str, int]`
- `apply_background_bonuses(scores: dict[str, int], background: str) -> tuple[dict[str, int], list[str]]`
- `ancestry_speed(ancestry: str) -> int`

### Files likely to change
- `src/dndnd/domain/characters.py`
- `src/dndnd/rules.py` (if trait tables need refinement)
- `tests/test_random_character.py`

### Acceptance criteria
- Human adds +1 to three distinct scores.
- Other ancestries apply the correct +2/+1 or special speed bonuses (e.g., Goliath 35 ft).
- Backgrounds add their fixed +2/+1 pair.
- No score exceeds 20 after bonuses.
- Bonus application is order-independent (e.g., background then ancestry yields the same final cap as ancestry then background).

### Validation steps
- Deterministic tests for each ancestry and a sample of backgrounds.
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1 and Sprint 2.

## Sprint 4 — Derived values and draft validation

### Objective
Compute the full set of derived statistics and provide a single validation entry point for the UI to call.

### Inputs
- Finalized ability scores, class name, ancestry, and level.
- Existing `proficiency_bonus_for_level`.

### Outputs
- `derive_values(scores, class_name, ancestry, level) -> DerivedValues`
- `validate_draft(draft: CharacterDraft) -> list[str]`

### Files likely to change
- `src/dndnd/domain/characters.py`
- `tests/test_random_character.py`

### Acceptance criteria
- AC = 10 + Dexterity modifier.
- Max HP = class hit die maximum + Constitution modifier, minimum 1.
- Speed comes from ancestry traits.
- Proficiency bonus is +2 at level 1.
- Passive perception = 10 + Wisdom modifier.
- Hit dice and spellcasting ability match the class.
- `validate_draft` returns human-readable errors for:
  - missing name
  - invalid ancestry or class
  - method-specific score violations
  - any score above 20
  - max HP <= 0
  - AC outside 1–40

### Validation steps
- Unit tests for derivation and validation edge cases.
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1, Sprint 2, and Sprint 3.

## Sprint 5 — Name generation and full draft builder

### Objective
Build a flavorful, collision-free name generator and a single `build_random_draft` orchestrator that the one-click flow can call.

### Inputs
- Domain functions from Sprints 1–4.
- Campaign character names for collision avoidance.

### Outputs
- `generate_name(existing_names: set[str], rng: random.Random) -> str`
- `build_random_draft(campaign, players, rng) -> CharacterDraft`
- `random_concept(rng: random.Random) -> str`

### Files likely to change
- `src/dndnd/domain/characters.py`
- `tests/test_random_character.py`

### Acceptance criteria
- Names avoid duplicates against the provided set; the generator retries on collision.
- Names are fantasy-style, not raw slugs.
- `build_random_draft` returns a level-1 draft with:
  - random identity fields
  - ability scores generated and placed by class priority
  - ancestry and background bonuses applied
  - derived values computed
  - starting class feature populated
  - a random concept
- The function is fully deterministic when seeded.

### Validation steps
- Deterministic tests for name collision avoidance and full draft structure.
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1, Sprint 2, Sprint 3, and Sprint 4.

## Sprint 6 — Repository persistence helper and provenance column

### Objective
Add a persistence helper that converts a `CharacterDraft` into model rows and store the ability-score method on the sheet.

### Inputs
- `CharacterDraft` from Sprint 1.
- `build_random_draft` from Sprint 5.
- Existing `CharacterRepository` and SQLAlchemy models.

### Outputs
- `CharacterRepository.exists_name_in_campaign(session, campaign_id, name) -> bool`
- `CharacterRepository.create_from_draft(session, campaign_id, draft) -> Character`
- `CharacterSheet.ability_score_method` column
- SQLite migration in `initialize_database` for existing databases

### Files likely to change
- `src/dndnd/data/repositories/characters.py`
- `src/dndnd/models.py`
- `src/dndnd/db.py`
- `tests/test_repositories.py`

### Acceptance criteria
- `exists_name_in_campaign` performs a case-insensitive uniqueness check.
- `create_from_draft` creates:
  - a `Character` row
  - a `CharacterSheet` row with the method provenance, background, alignment, speed, proficiency bonus, passive perception, hit dice, spellcasting ability, and notes
  - six `CharacterAbility` rows with scores, modifiers, and save bonuses
  - class starting feature as a `CharacterFeature`
- Existing SQLite databases gain the new `ability_score_method` column on startup.

### Validation steps
- Repository unit tests using an in-memory SQLite session.
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1 and Sprint 5.

## Sprint 7 — Test migration and focused domain unit tests

### Objective
Move the existing randomizer tests from the wrong layer to the domain module and add focused deterministic coverage for the new behavior.

### Inputs
- Domain functions from Sprints 1–5.
- Existing `tests/test_random_character.py`.

### Outputs
- Updated `tests/test_random_character.py` that imports from `dndnd.domain.characters` instead of `dndnd.app`.
- New tests covering:
  - each ability-score method
  - class-aware placement
  - ancestry and background bonuses
  - derived values
  - name collision avoidance
  - `validate_draft` error cases

### Files likely to change
- `tests/test_random_character.py`

### Acceptance criteria
- No test imports from `dndnd.app` for character generation.
- Every new domain function added in Sprints 1–5 has at least one deterministic test.
- Tests assert structural properties where exact values depend on data tables.

### Validation steps
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`

### Dependencies
- Sprint 1, Sprint 2, Sprint 3, Sprint 4, Sprint 5, and Sprint 6 (if any test exercises campaign-scoped name uniqueness or repository interaction).

## Sprint 8 — UI refactor: replace inline business rules

### Objective
Refactor `party.py` to delegate all generation, derivation, and validation to the domain layer, and remove the re-exports from `app.py`.

### Inputs
- Domain functions from Sprints 1–5.
- Repository helpers from Sprint 6.
- Updated tests from Sprint 7.

### Outputs
- `src/dndnd/ui/pages/party.py` imports domain helpers and uses them for:
  - one-click random character
  - ability-score rolling
  - point-buy validation
  - derived combat statistics
  - draft validation before persistence
- All inline tables (`HIT_DICE`, `SPELLCASTING_ABILITIES`, `RANDOM_FEATURES`, `BACKGROUND_OPTIONS`, etc.) removed from `party.py`.
- `src/dndnd/app.py` no longer re-exports `random_character_draft`, `generate_ability_scores`, `point_buy_total`, `build_roll_board`, or `POINT_BUY_BUDGET`.

### Files likely to change
- `src/dndnd/ui/pages/party.py`
- `src/dndnd/app.py`

### Acceptance criteria
- One-click "Roll random character" produces a draft via `build_random_draft`.
- Guided flow still supports all four ability-score methods and enforces the 27-point budget.
- Point-buy total uses `domain.point_buy_total`.
- Derived values use `domain.derive_values`.
- Draft validation uses `domain.validate_draft`.
- No business-rule tables remain in `party.py`.

### Validation steps
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- Manual smoke test: start the app and generate one random and one guided character.

### Dependencies
- Sprint 1, Sprint 2, Sprint 3, Sprint 4, Sprint 5, Sprint 6, and Sprint 7.

## Sprint 9 — Preview card, Regenerate, and Lock identity/abilities

### Objective
Add the builder-style UX affordances: a preview card before persistence, Regenerate, and lock toggles for identity and abilities.

### Inputs
- Refactored interview flow from Sprint 8.
- `build_random_draft` and `validate_draft` from the domain.

### Outputs
- A preview card rendered after step 3 (or before the final story step) showing name, ancestry, class, ability scores, modifiers, AC, HP, speed, and derived values.
- Lock controls for "identity" and "ability scores" that are stored in `st.session_state`.
- Regenerate button that re-runs `build_random_draft` while preserving locked fields.
- Final persistence uses `CharacterRepository.create_from_draft`.

### Files likely to change
- `src/dndnd/ui/pages/party.py`

### Acceptance criteria
- Preview card is visible before the character is saved.
- Regenerate produces a new draft but keeps locked identity fields (name, ancestry, class, background, concept) when identity is locked.
- Regenerate keeps locked ability scores when abilities are locked.
- Unlocked Regenerate produces a fully new draft.
- Saving persists the previewed draft unchanged through `create_from_draft`.
- Lock flags and the current draft are stored as separate `st.session_state` entries; `build_random_draft` is the only source of draft regeneration logic and no domain logic leaks into `session_state`.

### Validation steps
- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- Manual smoke test: generate, lock identity, regenerate, lock abilities, regenerate, save, and verify the persisted sheet.

### Dependencies
- Sprint 8.

## Risks, blockers, and open questions

### Risks
- **Scope creep:** ancestry and background tables can expand indefinitely (lineages, subspecies, feat grants). The tables should start with the 2024 Player's Handbook baseline and only grow through explicit follow-up ADRs.
- **UI state complexity:** Lock and Regenerate require careful `st.session_state` bookkeeping. Lock flags and the current draft should be stored separately, and the UI must never let domain logic leak back into session state.
- **Temporary duplication:** Sprints 1–6 add new rules tables while `party.py` still contains the old inline tables. This is intentional to keep each sprint green, but the duplicate tables must be removed in Sprint 8.
- **Name generator quality:** A small syllable-based generator is sufficient for the randomizer, but it may need tuning once used in play. Quality improvements should be a follow-up, not part of this plan.

### Blockers
- None identified. All work is local and self-contained.

### Open questions
1. Should the user be allowed to override the fixed background +2/+1 pair at generation time? This plan assumes a fixed pair per background.
2. Should raw pre-bonus scores and ancestry/background order be persisted for auditability, or is the method name enough? This plan persists only the method name.
3. Should name uniqueness be enforced at the database level with a unique constraint, or is the current case-insensitive repository check sufficient? This plan uses the repository helper only.

## Suggested order of execution

1. Sprint 1 — Domain model and static rules tables
2. Sprint 2 — Ability-score generation and class-aware assignment
3. Sprint 3 — Ancestry and background bonuses
4. Sprint 4 — Derived values and draft validation
5. Sprint 5 — Name generation and full draft builder
6. Sprint 6 — Repository persistence helper and provenance column
7. Sprint 7 — Test migration and focused domain unit tests
8. Sprint 8 — UI refactor: replace inline business rules
9. Sprint 9 — Preview card, Regenerate, and Lock identity/abilities

## Summary

- **Plan file:** `plans/character-randomizer-sprint-plan.md`
- **Sprints:** 9 focused sprints, moving from domain dataclasses and static rules through ability-score generation, ancestry/background bonuses, derivation, validation, name generation, repository persistence, test migration, and finally a UI refactor with preview/regenerate/lock affordances.
- **Key deliverables:** a rich `CharacterDraft` domain model, deterministic `random.Random`-based generators, collision-free fantasy names, a repository `create_from_draft` helper, and a `party.py` that only handles presentation and persistence.
- **Validation gate:** every sprint ends with `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` passing.
