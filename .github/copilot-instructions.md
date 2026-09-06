# DNDND development guidance

- Target Python 3.12 and use `uv` for environments and dependencies.
- Keep the app local-first. Never transmit campaign data except to the configured Ollama endpoint.
- Keep Streamlit rendering in `app.py`, persistence in `db.py`/`models.py`, and model calls in `llm.py`.
- Add typed SQLAlchemy 2.x models and focused pytest coverage for behavior changes.
- Run `ruff check`, `mypy src`, and `pytest` before considering a change complete.