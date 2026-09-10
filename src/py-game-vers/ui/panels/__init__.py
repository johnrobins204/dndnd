# ui/panels/__init__.py
"""
Panel subpackage exports.

Expose panel classes used by scenes so callers can import:
    from ui.panels import TablePanel, ChatPanel, CharacterPanel, QuestPanel
"""

__all__ = ["table_panel", "chat_panel", "character_panel", "quest_panel"]

from .character_panel import CharacterPanel  # noqa: F401
from .chat_panel import ChatPanel  # noqa: F401
from .quest_panel import QuestPanel  # noqa: F401
from .table_panel import TablePanel  # noqa: F401
