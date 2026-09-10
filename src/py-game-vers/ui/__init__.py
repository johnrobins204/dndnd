# ui/__init__.py
"""
UI package exports and convenience imports.

Keep this file minimal: expose commonly used classes for easier imports
(e.g., from ui import GameWindow, MainMenuScene).
Avoid heavy imports that initialize pygame at import time.
"""

__all__ = [
    "window",
    "scenes",
    "widgets",
    "styles",
    "panels",
]

# Lightweight re-exports for convenience (import modules, not heavy objects)
from . import (
    panels,  # noqa: F401
    scenes,  # noqa: F401
    styles,  # noqa: F401
    widgets,  # noqa: F401
    window,  # noqa: F401
)
