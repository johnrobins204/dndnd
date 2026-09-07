# DNDND development guidance

## Project Guidelines

- Target Python 3.12 and use `uv` for environments and dependencies.
- Keep the app local-first. Never transmit campaign data except to the configured Ollama endpoint.
- Keep Streamlit bootstrap in `app.py`, page rendering in `src/dndnd/ui/`, persistence in `db.py`/`models.py`/`src/dndnd/data/`, business rules in `src/dndnd/domain/`, and model calls in `llm.py`/`src/dndnd/intelligence/`.
- Add typed SQLAlchemy 2.x models, repository/domain boundaries for repeated behavior, and focused pytest coverage for behavior changes.
- Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` before considering a change complete.

## Registered Agents

The following agents are available for orchestrated workflows. They live in `.github/agents/` and are intended to be invoked by the Project Manager orchestrator.

### Project Manager
- **Use when:** A user wants to turn a feature request into implemented code through requirements definition, architectural review, sprint planning, and supervised development for Kimi K2.7 Code.
- **Role:** Entry-point orchestrator. Restates requirements for user approval, then coordinates Enterprise Architect, Sprint Planner, and Senior Developer.
- **Tools:** read, agent, todo, create_file.
- **Allowed subagents:** Enterprise Architect, Sprint Planner, Senior Developer.

### Enterprise Architect
- **Use when:** A project manager orchestrator needs architectural patterns evaluated, selected, or proposed within project constraints for Kimi K2.7 Code.
- **Output:** Architecture Decision Records (ADRs) in `docs/adr/`.
- **Tools:** read, search, web, create_file.

### Sprint Planner
- **Use when:** A project manager orchestrator needs a codebase-sized delivery plan broken into manageable sprints for Kimi K2.7 Code.
- **Output:** Sprint plans in `plans/`.
- **Tools:** read, search, web, create_file.

### Senior Developer
- **Use when:** A project manager orchestrator needs a senior developer to execute a sprint plan, supervise implementation quality, enforce project standards, and coordinate worker agents for Kimi K2.7 Code.
- **Output:** Implemented, reviewed, and validated code changes.
- **Tools:** read, search, edit, execute, agent, todo.
- **Allowed subagents:** Enterprise Architect.
