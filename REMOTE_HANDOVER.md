# DNDND Remote Handover

## Purpose

DNDND is a local-first D&D 5e (2024) dungeon master's workspace built with Python,
Streamlit, SQLite, SQLAlchemy, and a local Ollama endpoint.

The application manages:

- Campaigns and campaign briefing
- Characters and guided character creation
- 2024 classes, species, alignment, ability scores, and combat state
- Character journals, inventories, and features
- World creation and existing-world additions
- Quests, chapters, objectives, triggers, rewards, items, and NPC links
- Session transcripts and combat tracking
- Generated session scripts through Ollama

## Important Git State

The configured remote is:

```text
https://github.com/johnrobins204/dndnd.git
```

The default branch is `main`.

At handover time, the local working tree contains substantial uncommitted work,
including the World Builder, quest planning, refactor modules, and architecture
boundaries. A fresh clone from `origin/main` may not contain those local changes.
Confirm the remote commit before assuming the clone matches this workspace.

From the source workspace, inspect unpublished work with:

```powershell
git status --short
git diff --stat
git log --oneline --decorate -5
```

Do not discard or reset the local worktree without explicit approval. If the remote
must receive the current implementation, commit and push the intended changes from
the source workspace first, then pull them on the remote.

## Fresh Remote Clone

On the remote Windows machine:

```powershell
git clone https://github.com/johnrobins204/dndnd.git
Set-Location dndnd
git switch main
git pull --ff-only origin main
```

If the repository is already present:

```powershell
Set-Location C:\path\to\dndnd
git fetch origin
git status --short
git pull --ff-only origin main
```

If `git pull --ff-only` refuses because of local changes, stop and inspect them.
Do not use destructive reset commands unless the owner explicitly authorizes it.

## Requirements

- Windows PowerShell
- Git
- Python 3.12
- `uv`
- Ollama running on the configured local/network endpoint for generation features

The repository pins Python 3.12 in `.python-version` and declares `>=3.12` in
`pyproject.toml`.

Install `uv` if needed:

```powershell
py -3.11 -m pip install --user uv
```

The launcher may be Python 3.11 while `uv` provisions the project interpreter at
Python 3.12.

## Environment Setup

From the repository root:

```powershell
py -3.11 -m uv sync
Copy-Item .env.example .env
```

Edit `.env` as required:

```dotenv
DNDND_DATABASE_URL=sqlite:///data/dndnd.db
DNDND_OLLAMA_URL=http://localhost:11434
DNDND_OLLAMA_MODEL=mistral
DNDND_REQUEST_TIMEOUT_SECONDS=180
```

Campaign data is local. The application should only send generation prompts to the
configured Ollama endpoint. Do not add campaign data, `.env`, or `data/` to Git.

## Start The Application

```powershell
py -3.11 -m uv run dndnd
```

Open:

```text
http://localhost:8501
```

Equivalent direct command:

```powershell
.\.venv\Scripts\streamlit.exe run src/dndnd/app.py --server.headless true
```

If a previous Streamlit process is holding the port or an editable package lock,
stop that local process and restart the app. Do not run multiple copies against the
same database during development.

## Ollama

The default endpoint is `http://localhost:11434` and the default model is `mistral`.
Verify Ollama independently on the remote machine before testing Writer:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags
```

If Ollama is on another LAN host, set `DNDND_OLLAMA_URL` to that host. Keep the
endpoint private and reachable only from the intended local network.

## Validation Commands

Run from the repository root:

```powershell
py -3.11 -m uv run pytest
py -3.11 -m uv run ruff check .
py -3.11 -m uv run mypy src
```

The expected baseline is a green test suite, clean Ruff output, and clean strict
mypy output. Also verify the app endpoint:

```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8501).StatusCode
```

Expected result: `200`.

## Data And Schema

SQLite defaults to `data/dndnd.db`. The `data/` directory is ignored by Git.
The current application initializes missing SQLAlchemy tables at startup using
`Base.metadata.create_all`. Existing databases receive newly added tables, but this
is not a substitute for a complete migration history.

Before changing model relationships or removing columns:

1. Back up `data/dndnd.db`.
2. Run the test suite against an in-memory SQLite database.
3. Check existing local data compatibility.
4. Prefer Alembic migrations for destructive or column-changing changes.

Do not delete the local database to solve application errors without first making a
backup.

## Current Architecture

The active Streamlit bootstrap is in `src/dndnd/app.py`. Extracted UI boundaries are
under `src/dndnd/ui/`:

- `ui/theme.py`: theme CSS and campaign visual primitives
- `ui/navigation.py`: workspace rail
- `ui/campaign.py`: campaign selection and creation
- `ui/pages/briefing.py`: briefing page
- `ui/pages/table.py`: live session table
- `ui/pages/journal.py`: campaign journal
- `ui/pages/combat.py`: combat tracker
- `ui/pages/writer.py`: generation workflow
- `ui/pages/party.py`: current compatibility boundary
- `ui/pages/world.py`: current compatibility boundary
- `ui/pages/quests.py`: current compatibility boundary

Data boundaries:

- `src/dndnd/models.py`: typed SQLAlchemy models
- `src/dndnd/db.py`: engine, session scope, table bootstrap
- `src/dndnd/data/repositories/`: repositories for campaigns, characters, sessions,
  worlds, and quests

Domain boundaries:

- `domain/characters.py`: point buy and level-derived calculations
- `domain/worlds.py`: world checks and export boundary
- `domain/quests.py`: quest question boundary
- `domain/sessions.py`: session state boundary

Intelligence boundaries:

- `intelligence/client.py`: Ollama transport protocol and implementation
- `intelligence/prompts.py`: prompt exports
- `intelligence/world_guide.py`: bounded world guidance prompt boundary
- `intelligence/quest_guide.py`: quest guidance boundary
- `intelligence/writer.py`: writer prompt boundary

The detailed architecture roadmap is in [REFACTOR_PLAN.md](REFACTOR_PLAN.md).
World-building requirements are in [WORLD_BUILDING_PLAN.md](WORLD_BUILDING_PLAN.md).
Quest elicitation requirements are in [QUEST_BUILDING_PLAN.md](QUEST_BUILDING_PLAN.md).

## Remaining Refactor Work

The repository is structurally improved but not fully decomposed.

Remaining work:

- Move Party implementation out of `app.py`.
- Move World Builder and acceptance workflows out of `app.py`.
- Move Quest Builder out of `app.py`.
- Remove compatibility bridges in `ui/pages/party.py`, `world.py`, and `quests.py`.
- Add complete repositories for all repeated page queries.
- Move character/world/quest mutations into domain services.
- Expand intelligence guide services beyond prompt boundaries.
- Update the older `.github/copilot-instructions.md` wording so it reflects the
  extracted UI/data/intelligence architecture.
- Add or formalize Alembic migrations before schema evolution becomes destructive.

## Development Rules

- Keep Streamlit rendering in UI modules.
- Keep SQLAlchemy queries in repositories/data modules.
- Keep business rules in domain modules.
- Keep Ollama calls in intelligence modules.
- Never transmit campaign data anywhere except the configured Ollama endpoint.
- Treat generated output as draft until explicitly accepted.
- Preserve user data and existing worktree changes.
- Do not use destructive Git commands to resolve conflicts.
- Add focused tests for behavior changes.

## Suggested First Remote Task

After cloning and validating the app, finish the refactor in this order:

1. Extract Party internals and guided character creation.
2. Extract World Builder, draft persistence, review, and acceptance.
3. Extract Quest Builder and quest draft acceptance.
4. Remove the compatibility implementations from `app.py`.
5. Add repository/service boundary tests.
6. Run the full validation commands and verify the Streamlit browser flow.
