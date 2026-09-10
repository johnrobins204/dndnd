# ui/panels/character_panel.py
"""
CharacterPanel: renders a scrollable list of character cards and provides
basic interactions (select, open editor, quick actions).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, cast

import pygame

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ui.scenes import CharacterEditorScene  # type: ignore

from ui.styles import COLORS, FONT, METRICS
from ui.widgets import ScrollList


class CharacterCardRenderer:
    """
    Renderer function used by ScrollList to draw each character entry.
    """

    def __init__(self, on_click: Optional[Callable[[int], None]] = None):
        self.on_click = on_click
        self.title_font = FONT["normal"]
        self.small_font = FONT["small"]

    def __call__(
        self,
        surface: pygame.Surface,
        item: dict,
        rect: tuple[int, int, int, int],
        index: int,
    ) -> None:
        x, y, w, h = rect
        radius = METRICS.get("card_radius", 6)

        pygame.draw.rect(surface, COLORS.get("card_bg", (34, 34, 42)), (x, y, w, h), border_radius=radius)

        name = item.get("name", "Unnamed")
        name_surf = self.title_font.render(name, True, COLORS["accent"])
        surface.blit(name_surf, (x + 10, y + 8))

        cls = item.get("class_name", item.get("class", "Unknown"))
        lvl = item.get("level", 1)
        hp = f"{item.get('current_hp', 0)}/{item.get('max_hp', 0)}"
        info = f"{cls}  L{lvl}   HP {hp}"
        info_surf = self.small_font.render(info, True, COLORS["muted"])
        surface.blit(info_surf, (x + 10, y + 36))

        hint_surf = self.small_font.render("Edit", True, COLORS["button_text"])
        surface.blit(hint_surf, (x + w - 10 - hint_surf.get_width(), y + (h - hint_surf.get_height()) // 2))


class CharacterPanel:
    """
    High-level panel that composes a ScrollList of characters.
    """

    def __init__(self, services: Optional[dict] = None):
        self.services = services or {}
        self._load_characters_from_service()

        self._renderer = CharacterCardRenderer(on_click=self._on_card_click)

        # Cast fixes the renderer type mismatch for Pylance/ruff
        renderer_callable = cast(
            Callable[[pygame.Surface, object, tuple[int, int, int, int], int], None],
            lambda s, item, rect, idx: self._renderer(s, item, rect, idx),
        )

        self.scroll_list = ScrollList(items=self.characters, renderer=renderer_callable)

        self.selected_index: Optional[int] = None
        self._last_rect: Optional[tuple[int, int, int, int]] = None

    def _load_characters_from_service(self) -> None:
        repo = None
        repos = self.services.get("repos") or self.services
        if isinstance(repos, dict):
            repo = repos.get("character") or repos.get("character_repo")

        try:
            if repo and hasattr(repo, "list"):
                chars = repo.list()
                self.characters = chars if isinstance(chars, list) else []
                return
        except Exception:
            pass

        self.characters = [
            {"id": 1, "name": "Aria Swift", "class_name": "Rogue", "level": 3, "current_hp": 18, "max_hp": 18},
            {"id": 2, "name": "Borin Stone", "class_name": "Fighter", "level": 2, "current_hp": 22, "max_hp": 22},
            {"id": 3, "name": "Cora Light", "class_name": "Cleric", "level": 4, "current_hp": 16, "max_hp": 28},
            {"id": 4, "name": "Drel", "class_name": "Wizard", "level": 5, "current_hp": 12, "max_hp": 32},
            {"id": 5, "name": "Etta", "class_name": "Ranger", "level": 2, "current_hp": 14, "max_hp": 14},
        ]

    def refresh(self) -> None:
        self._load_characters_from_service()
        self.scroll_list.items = self.characters

    def set_characters(self, chars: list[dict]) -> None:
        self.characters = list(chars)
        self.scroll_list.items = self.characters
        self.selected_index = None

    def add_character(self, char: dict) -> None:
        self.characters.append(char)
        self.scroll_list.items = self.characters

    def remove_character_at(self, index: int) -> None:
        if 0 <= index < len(self.characters):
            del self.characters[index]
            self.scroll_list.items = self.characters
            if self.selected_index == index:
                self.selected_index = None

    def _on_card_click(self, index: int) -> None:
        win = self.services.get("window")
        if not win:
            return

        try:
            from ui.scenes import CharacterEditorScene  # local import avoids circular dependency

            char_id = self.characters[index].get("id")
            win.push_scene(CharacterEditorScene(self.services, character_index=index, character_id=char_id))
        except Exception:
            try:
                from ui.scenes import CharacterEditorScene
                win.push_scene(CharacterEditorScene(self.services, character_index=index))
            except Exception:
                logger.exception("Failed to open CharacterEditorScene")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.scroll_list.handle_event(event)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self._last_rect:
                return

            rx, ry, rw, rh = self._last_rect
            mx, my = event.pos

            if not (rx <= mx <= rx + rw and ry <= my <= ry + rh):
                return

            pad = METRICS.get("panel_padding", 8)
            item_h = METRICS.get("character_card_height", 64)
            item_pad = METRICS.get("character_card_gap", 6)

            content_y = my - (ry + pad) + int(self.scroll_list.scroll)
            idx = content_y // (item_h + item_pad)

            if 0 <= idx < len(self.characters):
                self.selected_index = idx
                try:
                    if callable(self._renderer.on_click):
                        self._renderer.on_click(idx)
                except Exception:
                    self._on_card_click(idx)

    def update(self, dt: float) -> None:
        self.scroll_list.update(dt)

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        self._last_rect = rect
        x, y, w, h = rect
        pad = METRICS.get("panel_padding", 8)

        pygame.draw.rect(surface, COLORS.get("panel_bg", (28, 28, 36)), (x, y, w, h))

        title_surf = FONT["normal"].render("Characters", True, COLORS["accent"])
        surface.blit(title_surf, (x + pad, y + pad))

        title_h = title_surf.get_height()
        list_rect = (x + pad, y + pad + title_h + pad, w - pad * 2, h - (pad * 3 + title_h))

        self.scroll_list.items = self.characters
        self.scroll_list.render(surface, list_rect)

        if self.selected_index is not None:
            item_h = METRICS.get("character_card_height", 64)
            item_pad = METRICS.get("character_card_gap", 6)

            y_cursor = list_rect[1] - int(self.scroll_list.scroll) + self.selected_index * (item_h + item_pad)
            sel_rect = pygame.Rect(list_rect[0], y_cursor, list_rect[2], item_h)

            if sel_rect.bottom >= list_rect[1] and sel_rect.top <= list_rect[1] + list_rect[3]:
                overlay = pygame.Surface((sel_rect.width, sel_rect.height), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, 18))
                surface.blit(overlay, sel_rect.topleft)
                pygame.draw.rect(surface, (200, 200, 200), sel_rect, width=1, border_radius=METRICS.get("card_radius", 6))
