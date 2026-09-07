# ADR 001: Established Patterns and Starting Architecture

## Status
Accepted

## Context

DNDND is a local-first D&D campaign assistant built with Python 3.12, Streamlit, SQLAlchemy 2.x, and `uv`. The project has grown organically, and several patterns have emerged across the codebase. Before adding new features, we want to document the patterns already in use and establish a standardized starting architecture so future work remains consistent and maintainable.

## Constraints

- Local-first: campaign data must never be transmitted except to the configured Ollama endpoint.
- Python 3.12, typed where practical, with `uv` for environments and dependencies.
- Changes must pass `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- Layer boundaries are already declared in [AGENTS.md](../../AGENTS.md).

## Established patterns

### Layer boundaries

The high-level layers are already defined in [AGENTS.md](../../AGENTS.md):

- Streamlit bootstrap in `app.py`.
- Page rendering in `src/dndnd/ui/`.
- Persistence in `db.py`, `models.py`, and `src/dndnd/data/`.
- Business rules in `src/dndnd/domain/`.
- Model calls in `llm.py` and `src/dndnd/intelligence/`.

### Persistence

- SQLAlchemy 2.x typed models using `Mapped[...]` in [src/dndnd/models.py](../../src/dndnd/models.py).
- A context-managed `session_scope` in [src/dndnd/db.py](../../src/dndnd/db.py) for transaction boundaries.
- A growing set of repositories under [src/dndnd/data/repositories/](../../src/dndnd/data/repositories/).

### Repositories

- Stateless classes/functions that accept a `Session`.
- Return model instances or small dataclass read-models.
- Use `selectinload` for eager loading where needed.
- Examples:
  - [src/dndnd/data/repositories/games.py](../../src/dndnd/data/repositories/games.py)
  - [src/dndnd/data/repositories/sessions.py](../../src/dndnd/data/repositories/sessions.py)

### Intelligence / LLM integration

- [src/dndnd/intelligence/client.py](../../src/dndnd/intelligence/client.py) provides `OllamaClient`.
- An `IntelligenceClient` protocol supports testability and future swapping.
- Prompt builders are pure functions in [src/dndnd/prompting.py](../../src/dndnd/prompting.py) and [src/dndnd/intelligence/game_chat.py](../../src/dndnd/intelligence/game_chat.py).
- LLM output is treated as draft/suggestion; the UI decides whether to persist it.

### Testing

- In-memory SQLite for repository and model tests.
- Real `session_scope` and repository layer used in tests.
- Focused assertions on behavior, prompt content, and data shape.
- Examples:
  - [tests/test_repositories.py](../../tests/test_repositories.py)
  - [tests/test_prompting.py](../../tests/test_prompting.py)

## Inconsistencies and gaps

- **Repository coverage is uneven.** Several UI pages still query models directly instead of using repositories:
  - `src/dndnd/ui/pages/journal.py`
  - `src/dndnd/ui/pages/combat.py`
  - `src/dndnd/ui/pages/writer.py`
  - `src/dndnd/ui/pages/briefing.py`
- **The domain layer is thin.** Combat turn logic, character creation derivation, and quest-state rules currently live inside UI pages rather than in `src/dndnd/domain/`.
- **Dead/duplicate code exists.** `app.py` contains unused page references and duplicated theme logic. The root `src/dndnd/llm.py` appears to be a stale copy of the client now maintained in `src/dndnd/intelligence/client.py`.

## Decision

Adopt the following standardized starting architecture for all new features unless a specific ADR approves a deviation:

1. **UI page** (`src/dndnd/ui/pages/<feature>.py`)
   - Owns only Streamlit widgets, `st.session_state` access, and presentation.
   - Contains no business rules beyond simple input validation.
   - Calls domain functions and repositories; does not query models directly.

2. **Domain module** (`src/dndnd/domain/<feature>.py`)
   - Owns pure business rules, calculations, and validation.
   - Prefers dataclasses or model-free inputs where possible.
   - Keeps persistence and UI concerns out.

3. **Repository** (`src/dndnd/data/repositories/<feature>.py`)
   - Owns all reads and writes for the feature's aggregate(s).
   - Accepts a `Session`, returns model instances or small read-models.
   - Handles eager loading and query optimization.

4. **Intelligence module** (`src/dndnd/intelligence/<feature>.py` or shared prompt builders)
   - Owns prompt construction for the feature.
   - The UI calls `OllamaClient.generate()` and decides whether to persist the result.

### Standard flow

```
UI event → domain rule / validator → repository → model → commit
```

### When to deviate

- Pure read-only dashboards may use repository read-models or lightweight query helpers.
- Prototypes can inline queries temporarily, but they must be migrated into repositories before the change is considered complete.
- Performance-sensitive bulk operations may use documented raw queries, but still behind a repository method.

## Consequences

- New features will be easier to test, review, and maintain because responsibilities are clearly separated.
- Existing pages that bypass repositories or the domain layer are now technical debt and should be refactored incrementally.
- The domain layer must be guarded against becoming either a thin passthrough or a dumping ground for UI/DB concerns.

## Risks

- Refactoring existing pages to use repositories/domain consistently is a non-trivial chunk of work.
- Without discipline, the domain layer could accumulate UI or persistence concerns.
- `src/dndnd/models.py` will continue to grow; split it only when readability materially suffers.

## Related

- [AGENTS.md](../../AGENTS.md)
- [src/dndnd/data/repositories/](../../src/dndnd/data/repositories/)
- [src/dndnd/domain/](../../src/dndnd/domain/)
- [src/dndnd/intelligence/](../../src/dndnd/intelligence/)
