# ADR 002: Character Randomizer Architecture

## Status

Accepted

## Context

DNDND needs a polished level-1 D&D 5e (2024) character randomizer. The current implementation is split between `src/dndnd/ui/pages/party.py` and small helpers in `src/dndnd/domain/characters.py`, with `app.py` re-exporting UI functions so the writer page can reach them. The approved requirements expand the randomizer to support multiple ability-score methods, class-aware score placement, ancestry/background bonuses, correct derived statistics, collision-free names, and a builder-style preview before persistence.

This ADR defines where each responsibility should live so the feature aligns with the layer boundaries established in [ADR 001](001-established-patterns-and-starting-architecture.md) and [AGENTS.md](../../AGENTS.md).

## Constraints

- Local-first: no rules data or character data leaves the machine except to the configured Ollama endpoint.
- Python 3.12, typed where practical, with `uv` for environments and dependencies.
- All changes must pass `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- Layer boundaries from [AGENTS.md](../../AGENTS.md) and [ADR 001](001-established-patterns-and-starting-architecture.md) are binding:
  - UI in `src/dndnd/ui/`.
  - Persistence in `src/dndnd/data/`.
  - Business rules in `src/dndnd/domain/`.
  - Static rules references in `src/dndnd/rules.py`.
- Level 1 only; subclass, equipment, feat, and spell-list automation are out of scope.

## Current state and deviations from established patterns

### 1. Business rules live in the UI page

`src/dndnd/ui/pages/party.py` currently owns:

- `random_character_draft()` — class/ancestry/background randomization, base ability-score shuffle, derived value calculation, name generation, and feature selection.
- `generate_ability_scores()` — standard array and 4d6-drop-lowest generation.
- `point_buy_total()` — duplicated in the UI page even though a domain version exists.
- `HIT_DICE`, `HIT_DIE_SIZES`, `SPELLCASTING_ABILITIES`, `RANDOM_FEATURES` — rules tables inlined in the page.
- `BACKGROUND_OPTIONS` and `RANDOM_CONCEPTS` — content lists inlined in the page.
- Derived-value calculations (AC, max HP, speed, proficiency bonus, passive perception, spellcasting ability) computed inline during the interview.

This violates the ADR 001 decision that business rules belong in `src/dndnd/domain/`.

### 2. The domain layer is a thin fragment

`src/dndnd/domain/characters.py` only exports:

- `POINT_BUY_COSTS` and `POINT_BUY_BUDGET`
- `point_buy_total(scores)`
- `proficiency_bonus_for_level(level)`

It does not model ability-score methods, class priorities, ancestry/background bonuses, or a character draft, so the UI has no place to delegate these concerns.

### 3. `app.py` imports directly from a UI page

`src/dndnd/app.py` re-exports `random_character_draft`, `generate_ability_scores`, `point_buy_total`, and `build_roll_board` from `src/dndnd/ui/pages/party.py`. This breaks the layer boundary between bootstrap and pages, and it couples unrelated features to the party page's implementation.

### 4. Names are not collision-free or flavorful

The current name generator uses `coolname.generate_slug(2)` and capitalizes the parts. It does not check against existing character names in the campaign and can produce awkward compound names rather than fantasy-style names.

### 5. Tests target UI functions

`tests/test_random_character.py` imports `random_character_draft`, `generate_ability_scores`, `point_buy_total`, and `build_roll_board` from `dndnd.app` (which re-exports them from the UI page). The tests are behavior-focused but depend on the wrong layer, and they do not exercise class priorities, ancestry bonuses, or deterministic derivation.

### 6. Validation is ad-hoc

Validation is scattered across the interview forms:

- Point buy must spend exactly 27 points.
- Required identity fields are checked before continuing.
- Score ranges are constrained by widget min/max but not by a domain validator.

There is no single `validate_draft()` function that a test can call to assert correctness.

## Approved/surfaced patterns from the codebase

The following patterns are already accepted and should be reused:

- **Layer boundaries** (ADR 001, AGENTS.md): UI → domain → repository → model.
- **Pure domain functions** for calculations, e.g. `proficiency_bonus_for_level`.
- **Static rule references** in `src/dndnd/rules.py` via the `RuleReference` dataclass.
- **Repositories** as stateless classes accepting a `Session`, as in `CharacterRepository`.
- **Typed SQLAlchemy 2.x models** in `src/dndnd/models.py`.
- **Deterministic tests** using `random.seed(...)` and direct domain function calls.
- **Dataclass-based inputs/outputs** for domain logic where model-free boundaries improve testability.

## Candidate patterns considered

### Option A: Keep rules in the UI page and only extract helpers

Move only `point_buy_total` and `proficiency_bonus_for_level` into `domain/characters.py`, leave everything else in `party.py`, and continue re-exporting from `app.py`.

- Pros: smallest initial diff.
- Cons: violates ADR 001; duplicates rules across UI and tests; makes deterministic testing and future reuse (e.g., NPC batch generation) difficult. **Rejected.**

### Option B: Fat rules module, thin domain

Move all static tables (`HIT_DICE`, `SPELLCASTING_ABILITIES`, ancestry traits, backgrounds) into `src/dndnd/rules.py` and keep all calculation/derivation logic in `src/dndnd/domain/characters.py`.

- Pros: clear separation between static reference data and executable rules; `rules.py` already holds `RuleReference` collections.
- Cons: `rules.py` could grow into a data dump if not bounded; still needs a domain orchestrator to combine tables into a draft.
- Viable, but requires discipline to keep only reference data in `rules.py`.

### Option C: Rich domain model with draft dataclass

Introduce a `CharacterDraft` dataclass and a small set of pure functions in `src/dndnd/domain/characters.py`:

- `AbilityScoreMethod` enum.
- `ScoreGenerator` functions for each method.
- `CLASS_PRIORITIES` table.
- `ANCESTRY_TRAITS` and `BACKGROUND_BONUSES` tables.
- `derive_character(draft)` that computes modifiers, AC, HP, speed, proficiency, passive perception, hit dice, and spellcasting ability.
- `validate_draft(draft)` returning a list of validation errors.
- `generate_name(campaign_names, rng)` that produces flavorful names and avoids collisions.
- `build_random_draft(...)` that returns a fully populated `CharacterDraft`.

The UI page only translates widget state into a `CharacterDraft`, calls domain functions, and persists the result through the repository.

- Pros: fully aligns with ADR 001; easiest to test deterministically; supports one-click and guided flows with the same functions; enables future features (NPC batching, import/export) to reuse the same logic.
- Cons: requires more upfront design than Option A.
- **Recommended.**

## Decision

Adopt **Option C**: a rich, model-free domain module for character generation and derivation, with static rules tables living in `src/dndnd/rules.py` and the UI restricted to presentation and persistence orchestration.

### Proposed module responsibilities

#### `src/dndnd/domain/characters.py`

Owns all character generation and derivation logic. Exports:

- `AbilityScoreMethod` — `STANDARD_ARRAY`, `DICE_4D6_DROP_LOWEST`, `POINT_BUY`, `MANUAL`.
- `POINT_BUY_BUDGET`, `POINT_BUY_COSTS`, `POINT_BUY_MIN_SCORE`, `POINT_BUY_MAX_SCORE`.
- `CharacterDraft` — dataclass describing a work-in-progress character:
  - identity fields (name, kind, player_id, ancestry, class_name, level, background, alignment, concept)
  - ability method and ability scores
  - derived values (AC, max HP, speed, proficiency bonus, passive perception, hit dice, spellcasting ability)
  - feature lines and notes.
- `generate_ability_scores(method: AbilityScoreMethod, rng: random.Random) -> dict[str, int]`
- `assign_scores_by_class(scores: list[int], class_name: str) -> dict[str, int]`
- `apply_ancestry_bonuses(scores: dict[str, int], ancestry: str) -> dict[str, int]`
- `apply_background_bonuses(scores: dict[str, int], background: str) -> tuple[dict[str, int], list[str]]`
- `derive_values(scores: dict[str, int], class_name: str, ancestry: str, level: int) -> DerivedValues`
- `validate_draft(draft: CharacterDraft) -> list[str]`
- `generate_name(existing_names: set[str], rng: random.Random) -> str`
- `build_random_draft(campaign, players, rng: random.Random) -> CharacterDraft`
- `proficiency_bonus_for_level(level: int) -> int`
- `point_buy_total(scores: dict[str, int]) -> int`

All randomness is injected via `random.Random` so tests can seed it deterministically.

#### `src/dndnd/rules.py`

Owns static reference data only:

- `ANCESTRY_TRAITS` — mapping ancestry name to speed, ability bonuses, traits summary, and a `RuleReference`.
- `BACKGROUND_BONUSES` — mapping background name to ability bonus pair and suggested proficiencies.
- `CLASS_PRIORITIES` — mapping class name to ordered list of ability names for score placement.
- `HIT_DICE`, `SPELLCASTING_ABILITIES`, `STARTING_FEATURES` — replace the inline tables currently in `party.py`.

These tables are referenced by the domain functions but contain no executable logic.

#### `src/dndnd/ui/pages/party.py`

Owns only Streamlit presentation:

- Render the interview steps.
- Translate widget values into a `CharacterDraft`.
- Call `domain.characters.validate_draft()` and surface errors.
- Call `domain.characters.build_random_draft()` for one-click generation.
- Support **Regenerate** by re-running the domain builder while preserving locked fields.
- Support **Lock identity/abilities** by keeping user-edited fields out of the regenerated draft.
- Render the preview card from the draft before persistence.
- Persist through `CharacterRepository` / SQLAlchemy `Session`.

#### `src/dndnd/app.py`

Stop re-exporting character-generation functions from `party.py`. The writer page and any future callers should import domain utilities from `src/dndnd/domain/characters.py` if needed.

#### `src/dndnd/data/repositories/characters.py`

Owns persistence helpers:

- `find_by_name_for_campaign(...)` already exists and supports collision checking.
- Add `exists_name_in_campaign(session, campaign_id, name) -> bool` if needed for name generation.
- Add `create_from_draft(session, campaign_id, draft: CharacterDraft) -> Character` to centralize the construction of `Character`, `CharacterSheet`, `CharacterAbility`, and `CharacterFeature` rows.

### Standard flow

```
One-click:
UI Regenerate click
  → domain.build_random_draft(campaign, players, seeded_rng)
  → domain.derive_values / domain.validate_draft
  → UI preview card
  → repository.create_from_draft(session, campaign.id, draft)
  → commit

Guided:
UI widget changes
  → UI assembles CharacterDraft
  → domain.validate_draft
  → domain.derive_values (for preview)
  → UI preview card
  → repository.create_from_draft(session, campaign.id, draft)
  → commit
```

### Validation structure

`validate_draft()` returns a flat list of human-readable error strings. The UI maps these into `st.error()` calls. Rules to enforce:

- Name is non-empty and not already used in the campaign.
- Ancestry and class are from the allowed enumerations.
- Ability scores are within method-specific bounds:
  - Standard array: exactly the values `[15, 14, 13, 12, 10, 8]`.
  - 4d6 drop lowest: each score between 3 and 18.
  - Point buy: each score between 8 and 15 and total cost equals 27.
  - Manual: each score between 1 and 20.
- After ancestry/background bonuses, no score exceeds 20.
- Derived max HP is greater than 0.
- AC is between 1 and 40 (reasonable bounds for a level-1 character).

### Deterministic tests

Tests live in `tests/test_random_character.py` and import from `dndnd.domain.characters`. Each test that exercises randomness constructs a local `random.Random(seed)`:

```python
from dndnd.domain.characters import build_random_draft, generate_ability_scores, AbilityScoreMethod


def test_standard_array_assigns_class_priorities() -> None:
    rng = random.Random(42)
    draft = build_random_draft(campaign, players, rng)
    assert draft.level == 1
    # class primary ability should get the highest score, etc.
```

Test coverage should include:

- Each ability-score method produces valid scores.
- Class-aware assignment places the highest scores in priority order.
- Ancestry bonuses apply correctly and respect the 20 cap.
- Background bonuses apply correctly.
- Derived values are computed from finalized scores.
- Name generation avoids collisions within a campaign.
- `validate_draft()` catches invalid point-buy, duplicate names, and out-of-bounds scores.

## Migration/adoption steps

1. Create `CharacterDraft` dataclass and `AbilityScoreMethod` enum in `src/dndnd/domain/characters.py`.
2. Move static tables (`HIT_DICE`, `SPELLCASTING_ABILITIES`, ancestry/background/class-priority tables) from `party.py` into `src/dndnd/rules.py`.
3. Implement domain functions: score generation, class assignment, ancestry/background application, derivation, validation, and name generation.
4. Refactor `src/dndnd/ui/pages/party.py` to use the domain module; remove inline business rules.
5. Add `CharacterRepository.create_from_draft()` and any needed name-existence helpers.
6. Remove the re-exports from `src/dndnd/app.py`; update `tests/test_random_character.py` to import from `dndnd.domain.characters`.
7. Add deterministic unit tests for all new domain behavior.
8. Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Risks

- **Scope creep:** ancestry and background bonuses can become arbitrarily complex (lineages, subspecies, feat grants). The tables should start with the 2024 Player's Handbook baseline and expand only through explicit follow-up ADRs.
- **Migration size:** moving rules out of `party.py` touches the guided interview, the one-click generator, and `app.py`. The change should be done in one focused pass to avoid half-migrated state.
- **UI state complexity:** Regenerate/Lock identity/abilities requires careful `st.session_state` management. The UI should store the lock flags and the current draft separately; it must not let domain logic leak back into `session_state`.
- **Test fragility:** class priority tables are data, not logic; tests should assert structural properties (primary ≥ secondary ≥ tertiary) rather than exact scores unless a fixed seed is used.

## Open questions

1. Should background ability bonuses be fixed to a single recommended pair per background, or should the user be allowed to choose the pair at generation time?
2. Should we persist the provenance of ability-score method and the raw pre-bonus scores, or only the final scores and method name?
3. Do we need a repository-level uniqueness check for names, or is an in-memory set of existing campaign names sufficient for the randomizer?

## Related

- [ADR 001: Established Patterns and Starting Architecture](001-established-patterns-and-starting-architecture.md)
- [AGENTS.md](../../AGENTS.md)
- [plans/character-randomizer-delivery.md](../../plans/character-randomizer-delivery.md)
- [src/dndnd/domain/characters.py](../../src/dndnd/domain/characters.py)
- [src/dndnd/ui/pages/party.py](../../src/dndnd/ui/pages/party.py)
- [src/dndnd/rules.py](../../src/dndnd/rules.py)
- [src/dndnd/models.py](../../src/dndnd/models.py)
