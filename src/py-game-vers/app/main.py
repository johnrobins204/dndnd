# app/main.py
"""
Bootstrapper for the Pygame DnD DM application.

Responsibilities:
- Wire together repos, services, intelligence, and UI
- Seed sample data for local development (optional)
- Create GameWindow, push initial scene, and run main loop

Run:
    python -m app.main
"""

from __future__ import annotations

import argparse
import logging

from services.game_service import GameService
from services.session_service import SessionService
from services.tool_service import ToolService
from ui.scenes import MainMenuScene
from ui.window import GameWindow

# Ensure project package imports work when running as a module
from data.repos import DEFAULT_REPOS, make_default_repos, seed_sample_data

# Optional: import assets.config for configuration (window size, DB URL, etc.)
try:
    import assets.config as config  # type: ignore
except Exception:
    config = None

# Configure basic logging for the app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dnd_app")


def build_services(repos: dict, enable_tool_discovery: bool = True) -> dict:
    """
    Create and wire service instances used by the UI and scenes.
    Returns a dict of services keyed by conventional names.
    """
    # ToolService: provide default context with repos and (optionally) other clients
    tool_ctx = {"repos": repos}
    tool_svc = ToolService(default_context=tool_ctx, discover_on_init=enable_tool_discovery)

    # SessionService: uses repos and tool service for tool-backed actions
    session_svc = SessionService(repos={"session": repos.get("session")}, tool_service=tool_svc)

    # GameService: orchestrates games and sessions
    game_svc = GameService(
        repos={"game": repos.get("game"), "session": repos.get("session")}, tool_service=tool_svc
    )

    services = {
        "repos": repos,
        "tool": tool_svc,
        "session": session_svc,
        "game": game_svc,
    }
    return services


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="dnd_dm", description="Run the Pygame DnD DM console (development mode)."
    )
    p.add_argument("--seed", action="store_true", help="Seed sample data into in-memory repos")
    p.add_argument(
        "--no-tools", action="store_true", help="Disable tool discovery (faster startup)"
    )
    p.add_argument(
        "--width", type=int, default=getattr(config, "WINDOW_WIDTH", 1280), help="Window width"
    )
    p.add_argument(
        "--height", type=int, default=getattr(config, "WINDOW_HEIGHT", 720), help="Window height"
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Create repos (in-memory by default)
    try:
        repos = DEFAULT_REPOS if DEFAULT_REPOS else make_default_repos()
    except Exception:
        repos = make_default_repos()

    if args.seed:
        try:
            seed_sample_data(repos)
            logger.info("Seeded sample data into repos.")
        except Exception as e:
            logger.warning("Failed to seed sample data: %s", e)

    # Build services
    services = build_services(repos, enable_tool_discovery=not args.no_tools)

    # Create and run GameWindow
    try:
        window = GameWindow(
            services=services, width=args.width, height=args.height, caption="DnD DM Console"
        )
        # Push initial scene (MainMenuScene)
        window.push_scene(MainMenuScene(services=services))
        logger.info("Starting main loop.")
        window.run()
    except Exception as e:
        logger.exception("Unhandled exception in main loop: %s", e)
        # Ensure pygame quits on error
        try:
            import pygame

            pygame.quit()
        except Exception:
            pass
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
