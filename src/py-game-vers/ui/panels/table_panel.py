# ui/panels/table_panel.py
"""
TablePanel: renders the tabletop grid, tokens, and handles basic interactions.

Responsibilities:
- Render a tiled grid or background image
- Render tokens (PCs, NPCs) as simple colored circles or images
- Support pan and zoom (mouse drag + wheel)
- Support token selection and dragging
- Provide a small API for scenes/services to add/remove/update tokens

This is intentionally self-contained and UI-focused. Token persistence and
domain semantics belong to services/repos; the panel only keeps a local
presentation model and exposes hooks to synchronize with services.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame
from ui.styles import COLORS


# Simple token representation for the panel
@dataclass
class Token:
    id: str
    name: str
    x: float  # world coordinates
    y: float
    radius: float = 18.0
    color: tuple[int, int, int] = (200, 160, 80)
    image: pygame.Surface | None = None  # optional sprite
    selected: bool = False


class TablePanel:
    """
    TablePanel manages a viewport into a larger tabletop world.

    Coordinate systems:
      - world coordinates: floating point units used for token positions
      - screen coordinates: pixels inside the provided rect

    Interaction model:
      - Left click on a token selects it.
      - Left drag on a selected token moves it (in world coords).
      - Middle mouse drag (or right drag with modifier) pans the view.
      - Mouse wheel zooms in/out centered on cursor.
    """

    def __init__(self, world_width: int = 2000, world_height: int = 1600):
        # world size in "pixels" (arbitrary units)
        self.world_width = world_width
        self.world_height = world_height

        # viewport transform state
        self.offset_x = 0.0  # world coordinate at screen (0,0)
        self.offset_y = 0.0
        self.zoom = 1.0  # scale factor (1.0 = 1 world px -> 1 screen px)

        # grid settings
        self.grid_size = 64  # world units per grid cell
        self.grid_color = COLORS.get("grid_line", (60, 60, 60))

        # tokens keyed by id
        self.tokens: dict[str, Token] = {}

        # interaction state
        self._dragging_token_id: str | None = None
        self._drag_token_offset: tuple[float, float] = (0.0, 0.0)
        self._panning = False
        self._pan_start: tuple[int, int] = (0, 0)
        self._pan_start_offset: tuple[float, float] = (0.0, 0.0)

        # selection rectangle (for future multi-select)
        self._select_rect_start: tuple[int, int] | None = None
        self._select_rect_current: tuple[int, int] | None = None

        # appearance
        self.background_color = (30, 30, 40)

    # -------------------------
    # Public token API
    # -------------------------
    def add_token(self, token: Token) -> None:
        """Add or replace a token by id."""
        self.tokens[token.id] = token

    def remove_token(self, token_id: str) -> None:
        if token_id in self.tokens:
            del self.tokens[token_id]

    def get_token(self, token_id: str) -> Token | None:
        return self.tokens.get(token_id)

    def list_tokens(self) -> list[Token]:
        return list(self.tokens.values())

    def clear_tokens(self) -> None:
        self.tokens.clear()

    # -------------------------
    # Coordinate transforms
    # -------------------------
    def world_to_screen(
        self, wx: float, wy: float, rect: tuple[int, int, int, int]
    ) -> tuple[int, int]:
        """Convert world coords to screen coords inside rect."""
        rx, ry, rw, rh = rect
        sx = rx + (wx - self.offset_x) * self.zoom
        sy = ry + (wy - self.offset_y) * self.zoom
        return int(sx), int(sy)

    def screen_to_world(
        self, sx: int, sy: int, rect: tuple[int, int, int, int]
    ) -> tuple[float, float]:
        """Convert screen coords (absolute window coords) to world coords."""
        rx, ry, rw, rh = rect
        wx = self.offset_x + (sx - rx) / self.zoom
        wy = self.offset_y + (sy - ry) / self.zoom
        return wx, wy

    # -------------------------
    # Hit testing
    # -------------------------
    def _token_at_point(self, sx: int, sy: int, rect: tuple[int, int, int, int]) -> str | None:
        """Return token id under screen point, or None."""
        # iterate topmost first (in insertion order, last drawn on top)
        for tid in reversed(list(self.tokens.keys())):
            t = self.tokens[tid]
            tx, ty = self.world_to_screen(t.x, t.y, rect)
            r = max(6, int(t.radius * self.zoom))
            dx = sx - tx
            dy = sy - ty
            if dx * dx + dy * dy <= r * r:
                return tid
        return None

    # -------------------------
    # Event handling
    # -------------------------
    def handle_event(
        self, event: pygame.event.Event, rect: tuple[int, int, int, int] | None = None
    ) -> None:
        """
        Handle pygame events. If rect is None, the panel assumes full window.
        Scenes should pass the rect used for rendering so transforms are correct.
        """
        if rect is None:
            # default to full window
            rect = (
                0,
                0,
                pygame.display.get_surface().get_width(),
                pygame.display.get_surface().get_height(),
            )

        # Mouse button down
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left click: select / start dragging token
            if event.button == 1:
                tid = self._token_at_point(event.pos[0], event.pos[1], rect)
                if tid:
                    # start dragging token
                    self._dragging_token_id = tid
                    token = self.tokens[tid]
                    wx, wy = self.screen_to_world(event.pos[0], event.pos[1], rect)
                    self._drag_token_offset = (token.x - wx, token.y - wy)
                    # mark selection
                    for t in self.tokens.values():
                        t.selected = t.id == tid
                else:
                    # start selection rectangle
                    self._select_rect_start = event.pos
                    self._select_rect_current = event.pos
                    # clear selection
                    for t in self.tokens.values():
                        t.selected = False

            # Middle button or right button + ctrl: start panning
            elif event.button == 2 or (
                event.button == 3 and (pygame.key.get_mods() & pygame.KMOD_CTRL)
            ):
                self._panning = True
                self._pan_start = event.pos
                self._pan_start_offset = (self.offset_x, self.offset_y)

            # Mouse wheel handled in MOUSEWHEEL event (pygame 2)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                # finish dragging token or selection
                if self._dragging_token_id:
                    # notify potential listeners (not implemented here)
                    self._dragging_token_id = None
                if self._select_rect_start:
                    # compute selection rectangle in world coords and select tokens inside
                    sx0, sy0 = self._select_rect_start
                    sx1, sy1 = self._select_rect_current or self._select_rect_start
                    wx0, wy0 = self.screen_to_world(sx0, sy0, rect)
                    wx1, wy1 = self.screen_to_world(sx1, sy1, rect)
                    x0, x1 = sorted((wx0, wx1))
                    y0, y1 = sorted((wy0, wy1))
                    for t in self.tokens.values():
                        if x0 <= t.x <= x1 and y0 <= t.y <= y1:
                            t.selected = True
                    self._select_rect_start = None
                    self._select_rect_current = None
            elif event.button == 2 or (
                event.button == 3 and (pygame.key.get_mods() & pygame.KMOD_CTRL)
            ):
                self._panning = False

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self._dragging_token_id:
                # move token in world coords
                wx, wy = self.screen_to_world(mx, my, rect)
                token = self.tokens.get(self._dragging_token_id)
                if token:
                    token.x = wx + self._drag_token_offset[0]
                    token.y = wy + self._drag_token_offset[1]
            elif self._panning:
                dx = event.pos[0] - self._pan_start[0]
                dy = event.pos[1] - self._pan_start[1]
                self.offset_x = self._pan_start_offset[0] - dx / self.zoom
                self.offset_y = self._pan_start_offset[1] - dy / self.zoom
                self._clamp_offset()
            elif self._select_rect_start:
                self._select_rect_current = event.pos

        elif event.type == pygame.MOUSEWHEEL:
            # Zoom centered on mouse position
            # event.y is +1 for up, -1 for down
            mx, my = pygame.mouse.get_pos()
            # If rect provided, only zoom if mouse inside rect
            rx, ry, rw, rh = rect
            if not (rx <= mx <= rx + rw and ry <= my <= ry + rh):
                return
            old_zoom = self.zoom
            # scale factor per wheel tick
            factor = 1.15 if event.y > 0 else 1 / 1.15
            new_zoom = max(0.25, min(4.0, self.zoom * factor))
            # compute world coordinate under cursor and adjust offset so that point stays under cursor
            wx_before, wy_before = self.screen_to_world(mx, my, rect)
            self.zoom = new_zoom
            wx_after, wy_after = self.screen_to_world(mx, my, rect)
            # adjust offset to keep world point stable
            self.offset_x += wx_before - wx_after
            self.offset_y += wy_before - wy_after
            self._clamp_offset()

    # -------------------------
    # Update
    # -------------------------
    def update(self, dt: float) -> None:
        # Placeholder for animations or token effects
        pass

    # -------------------------
    # Rendering
    # -------------------------
    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        """
        Draw the table into the given rect.
        """
        rx, ry, rw, rh = rect
        # background
        pygame.draw.rect(surface, self.background_color, (rx, ry, rw, rh))

        # draw grid lines (world-aligned)
        # compute visible world bounds
        left_top = self.screen_to_world(rx, ry, rect)
        right_bottom = self.screen_to_world(rx + rw, ry + rh, rect)
        wx0, wy0 = left_top
        wx1, wy1 = right_bottom

        # find grid lines in range
        start_x = math.floor(wx0 / self.grid_size) * self.grid_size
        end_x = math.ceil(wx1 / self.grid_size) * self.grid_size
        start_y = math.floor(wy0 / self.grid_size) * self.grid_size
        end_y = math.ceil(wy1 / self.grid_size) * self.grid_size

        # vertical lines
        for gx in range(int(start_x), int(end_x) + 1, int(self.grid_size)):
            sx, _ = self.world_to_screen(gx, wy0, rect)
            pygame.draw.line(surface, self.grid_color, (sx, ry), (sx, ry + rh))

        # horizontal lines
        for gy in range(int(start_y), int(end_y) + 1, int(self.grid_size)):
            _, sy = self.world_to_screen(wx0, gy, rect)
            pygame.draw.line(surface, self.grid_color, (rx, sy), (rx + rw, sy))

        # draw tokens
        for tid, token in self.tokens.items():
            tx, ty = self.world_to_screen(token.x, token.y, rect)
            # skip tokens outside rect (simple culling)
            if tx + token.radius * self.zoom < rx or tx - token.radius * self.zoom > rx + rw:
                continue
            if ty + token.radius * self.zoom < ry or ty - token.radius * self.zoom > ry + rh:
                continue

            # draw token background (circle or image)
            r = max(4, int(token.radius * self.zoom))
            if token.image:
                try:
                    img = pygame.transform.smoothscale(token.image, (r * 2, r * 2))
                    surface.blit(img, (tx - r, ty - r))
                except Exception:
                    pygame.draw.circle(surface, token.color, (tx, ty), r)
            else:
                pygame.draw.circle(surface, token.color, (tx, ty), r)

            # selection ring
            if token.selected:
                pygame.draw.circle(surface, (255, 255, 255), (tx, ty), r + 4, width=2)

            # name label
            name_surf = FONT_SMALL = pygame.font.SysFont("Arial", 14).render(
                token.name, True, COLORS["text"]
            )
            surface.blit(name_surf, (tx - name_surf.get_width() // 2, ty + r + 4))

        # draw selection rectangle if active (screen coords)
        if self._select_rect_start and self._select_rect_current:
            x0, y0 = self._select_rect_start
            x1, y1 = self._select_rect_current
            rx0, ry0 = min(x0, x1), min(y0, y1)
            rw_sel, rh_sel = abs(x1 - x0), abs(y1 - y0)
            sel_rect = pygame.Rect(rx0, ry0, rw_sel, rh_sel)
            overlay = pygame.Surface((rw_sel, rh_sel), pygame.SRCALPHA)
            overlay.fill((100, 160, 240, 40))
            surface.blit(overlay, (rx0, ry0))
            pygame.draw.rect(surface, (100, 160, 240), sel_rect, width=2)

    # -------------------------
    # Helpers
    # -------------------------
    def _clamp_offset(self) -> None:
        """Ensure the viewport offset keeps the world in reasonable bounds."""
        # compute visible world size
        vw = self.width_in_world()
        vh = self.height_in_world()
        # clamp offset so viewport stays within world bounds
        self.offset_x = max(0, min(self.offset_x, max(0, self.world_width - vw)))
        self.offset_y = max(0, min(self.offset_y, max(0, self.world_height - vh)))

    def width_in_world(self) -> float:
        """Return how many world units fit horizontally in the viewport at current zoom.
        Note: caller must pass the rect width; here we assume full window width if available."""
        try:
            surf = pygame.display.get_surface()
            if surf:
                return surf.get_width() / self.zoom
        except Exception:
            pass
        return 1280 / self.zoom

    def height_in_world(self) -> float:
        try:
            surf = pygame.display.get_surface()
            if surf:
                return surf.get_height() / self.zoom
        except Exception:
            pass
        return 720 / self.zoom

    # Convenience: center viewport on a world point
    def center_on(
        self, wx: float, wy: float, rect: tuple[int, int, int, int] | None = None
    ) -> None:
        if rect is None:
            try:
                surf = pygame.display.get_surface()
                rect = (0, 0, surf.get_width(), surf.get_height())
            except Exception:
                rect = (0, 0, 1280, 720)
        rx, ry, rw, rh = rect
        self.offset_x = wx - (rw / 2) / self.zoom
        self.offset_y = wy - (rh / 2) / self.zoom
        self._clamp_offset()
