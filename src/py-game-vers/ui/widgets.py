# ui/widgets.py
"""
Reusable UI widgets for the pygame DnD DM UI.

Widgets follow a simple contract:
- handle_event(event): process pygame events (mouse, keyboard)
- update(dt): update internal state (animations, caret blink)
- render(surface, rect): draw the widget into the given rectangle

Widgets are intentionally minimal and callback-driven. They do not
perform domain actions directly; instead they call callbacks provided
by the scene or panel that composes them.
"""

from __future__ import annotations

from collections.abc import Callable

import pygame
from ui.styles import COLORS, FONT


# Helper
def _point_in_rect(pos: tuple[int, int], rect: tuple[int, int, int, int]) -> bool:
    x, y = pos
    rx, ry, rw, rh = rect
    return rx <= x <= rx + rw and ry <= y <= ry + rh


class Widget:
    """Base widget interface."""

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        pass


class Label(Widget):
    def __init__(
        self,
        text: str,
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] | None = None,
    ):
        self.text = text
        self.font = font or FONT["normal"]
        self.color = color or COLORS["text"]

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        surf = self.font.render(self.text, True, self.color)
        surface.blit(surf, (x, y))


class Button(Widget):
    def __init__(
        self,
        text: str,
        callback: Callable[[], None] | None = None,
        font: pygame.font.Font | None = None,
    ):
        self.text = text
        self.callback = callback
        self.font = font or FONT["normal"]
        self._rect: pygame.Rect | None = None
        self._hover = False
        self._pressed = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            if self._rect:
                self._hover = self._rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect and self._rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self._rect and self._rect.collidepoint(event.pos):
                # click
                if self.callback:
                    try:
                        self.callback()
                    except Exception:
                        # swallow exceptions from callbacks to avoid crashing UI
                        pass
            self._pressed = False

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._rect = pygame.Rect(x, y, w, h)
        color = COLORS["button_hover"] if self._hover or self._pressed else COLORS["button"]
        pygame.draw.rect(surface, color, self._rect, border_radius=6)
        txt = self.font.render(self.text, True, COLORS["button_text"])
        tx = x + (w - txt.get_width()) // 2
        ty = y + (h - txt.get_height()) // 2
        surface.blit(txt, (tx, ty))


class TextInput(Widget):
    """
    Single-line text input.

    Callers should check `value` when Enter is pressed or when needed.
    Provide an optional `on_submit` callback that receives the current text.
    """

    def __init__(
        self,
        placeholder: str = "",
        font: pygame.font.Font | None = None,
        on_submit: Callable[[str], None] | None = None,
    ):
        self.font = font or FONT["normal"]
        self.placeholder = placeholder
        self.value = ""
        self.active = False
        self._rect = pygame.Rect(0, 0, 0, 0)
        self._caret_visible = True
        self._caret_timer = 0.0
        self._on_submit = on_submit
        self._max_length = 1024

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self._rect.collidepoint(event.pos)
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self._on_submit:
                    try:
                        self._on_submit(self.value)
                    except Exception:
                        pass
                # keep text by default; caller may clear it
            elif event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key == pygame.K_TAB:
                # ignore tab in single-line input
                pass
            else:
                ch = event.unicode
                if ch and len(self.value) < self._max_length:
                    self.value += ch

    def update(self, dt: float) -> None:
        # blink caret
        self._caret_timer += dt
        if self._caret_timer >= 0.5:
            self._caret_visible = not self._caret_visible
            self._caret_timer = 0.0

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, COLORS["input_bg"], self._rect, border_radius=4)
        text_to_draw = self.value if self.value else self.placeholder
        color = COLORS["input_text"] if self.value else (140, 140, 140)
        txt_surf = self.font.render(text_to_draw, True, color)
        surface.blit(txt_surf, (x + 6, y + (h - txt_surf.get_height()) // 2))
        # caret
        if self.active and self._caret_visible:
            caret_x = x + 6 + txt_surf.get_width() + 1
            caret_y1 = y + 6
            caret_y2 = y + h - 6
            pygame.draw.line(
                surface, COLORS["button_text"], (caret_x, caret_y1), (caret_x, caret_y2), 2
            )


class ScrollList(Widget):
    """
    Vertical scroll list of items. Items are rendered by a provided renderer function.

    renderer(surface, item, rect, index) -> None
    """

    def __init__(
        self,
        items: list | None = None,
        renderer: Callable[[pygame.Surface, object, tuple[int, int, int, int], int], None]
        | None = None,
    ):
        self.items = items or []
        self.renderer = renderer
        self.scroll = 0  # pixel offset from top
        self._rect = pygame.Rect(0, 0, 0, 0)
        self._content_height = 0
        self._dragging = False
        self._drag_start_y = 0
        self._drag_start_scroll = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect.collidepoint(event.pos):
                self._dragging = True
                self._drag_start_y = event.pos[1]
                self._drag_start_scroll = self.scroll
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            dy = event.pos[1] - self._drag_start_y
            self.scroll = self._drag_start_scroll - dy
            self._clamp_scroll()
        elif event.type == pygame.MOUSEWHEEL:
            # pygame 2: event.y is scroll direction
            self.scroll -= event.y * 24
            self._clamp_scroll()

    def _clamp_scroll(self) -> None:
        max_scroll = max(0, self._content_height - self._rect.height)
        if self.scroll < 0:
            self.scroll = 0
        if self.scroll > max_scroll:
            self.scroll = max_scroll

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._rect = pygame.Rect(x, y, w, h)
        # background
        pygame.draw.rect(surface, (18, 18, 24), self._rect)
        # render items into a clipped surface
        clip = surface.subsurface(self._rect)
        clip.fill((18, 18, 24))
        pad = 6
        y_cursor = pad - self.scroll
        self._content_height = 0
        for idx, item in enumerate(self.items):
            item_rect = (pad, y_cursor, w - pad * 2, 64)
            if self.renderer:
                try:
                    self.renderer(clip, item, item_rect, idx)
                except Exception:
                    # swallow renderer errors to avoid breaking UI
                    pass
            y_cursor += 64 + pad
            self._content_height = y_cursor + pad
        # optional scrollbar
        if self._content_height > h:
            bar_h = max(24, int(h * (h / self._content_height)))
            max_scroll = self._content_height - h
            scroll_ratio = self.scroll / max_scroll if max_scroll > 0 else 0
            bar_y = int(scroll_ratio * (h - bar_h))
            bar_rect = pygame.Rect(x + w - 8, y + bar_y, 6, bar_h)
            pygame.draw.rect(surface, (80, 80, 90), bar_rect, border_radius=3)


class Card(Widget):
    """
    Generic card widget that renders a title and lines of text.
    Data is a dict-like object with keys used by the renderer.
    """

    def __init__(
        self, title: str, lines: list[str] | None = None, on_click: Callable[[], None] | None = None
    ):
        self.title = title
        self.lines = lines or []
        self.on_click = on_click
        self._rect: pygame.Rect | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect and self._rect.collidepoint(event.pos):
                if self.on_click:
                    try:
                        self.on_click()
                    except Exception:
                        pass

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (28, 28, 36), self._rect, border_radius=6)
        title_surf = FONT["normal"].render(self.title, True, COLORS["accent"])
        surface.blit(title_surf, (x + 8, y + 6))
        for i, line in enumerate(self.lines):
            line_surf = FONT["normal"].render(line, True, COLORS["text"])
            surface.blit(line_surf, (x + 8, y + 36 + i * (FONT["normal"].get_height() + 2)))
