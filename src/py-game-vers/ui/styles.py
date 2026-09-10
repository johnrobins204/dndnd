# ui/styles.py
"""
UI styles: fonts, colors, sizes, and small helpers.

This module centralizes visual constants so the rest of the UI can import:
    from ui.styles import FONT, COLORS, SIZES, load_font

Keep this file small and deterministic so tests and snapshots remain stable.
"""

from __future__ import annotations

import os

import pygame

# Ensure pygame font subsystem is initialized when this module is imported.
if not pygame.get_init():
    pygame.init()
if not pygame.font.get_init():
    pygame.font.init()

# Default font family fallback
_DEFAULT_FONT_NAME = "Arial"

# Font sizes used across the UI
SIZES: dict[str, int] = {
    "small": 14,
    "normal": 18,
    "large": 28,
    "title": 36,
}


# Helper to create a pygame Font object safely
def load_font(
    name: str | None, size: int, bold: bool = False, italic: bool = False
) -> pygame.font.Font:
    """
    Load a system font by name and size. Falls back to a default font if the requested
    font is not available. Use this for consistent font creation across the UI.
    """
    try:
        if name:
            return pygame.font.SysFont(name, size, bold=bold, italic=italic)
    except Exception:
        pass
    # fallback
    return pygame.font.SysFont(_DEFAULT_FONT_NAME, size, bold=bold, italic=italic)


# Pre-created font objects for convenience
FONT: dict[str, pygame.font.Font] = {
    "small": load_font(None, SIZES["small"]),
    "normal": load_font(None, SIZES["normal"]),
    "large": load_font(None, SIZES["large"]),
    "title": load_font(None, SIZES["title"], bold=True),
}

# Color palette (R, G, B)
COLORS: dict[str, tuple[int, int, int]] = {
    # Backgrounds
    "bg": (18, 18, 18),
    "menu_bg": (30, 30, 50),
    "game_bg": (24, 24, 30),
    # Text and accents
    "text": (230, 230, 230),
    "muted": (160, 160, 170),
    "accent": (200, 180, 80),
    # UI controls
    "button": (60, 60, 80),
    "button_hover": (90, 90, 120),
    "button_text": (255, 255, 255),
    "input_bg": (40, 40, 50),
    "input_text": (200, 200, 200),
    # Panels and cards
    "panel_bg": (28, 28, 36),
    "card_bg": (34, 34, 42),
    "grid_line": (60, 60, 60),
    # Status colors
    "hp_good": (80, 200, 120),
    "hp_warn": (240, 180, 60),
    "hp_bad": (220, 80, 80),
}

# Common sizes and spacing
METRICS = {
    "gutter": 8,
    "panel_padding": 12,
    "card_radius": 6,
    "button_radius": 6,
    "scrollbar_width": 8,
}


# Small utility helpers ----------------------------------------------------
def text_size(text: str, font: pygame.font.Font | None = None) -> tuple[int, int]:
    """Return (width, height) of rendered text using the provided font or default normal font."""
    f = font or FONT["normal"]
    surf = f.render(text, True, COLORS["text"])
    return surf.get_width(), surf.get_height()


# Optional: allow runtime theme override via environment variables
def _apply_env_overrides() -> None:
    """
    If environment variables are set (for quick theming during development),
    apply them. Supported vars:
      UI_BG, UI_ACCENT (hex color like #RRGGBB)
    """

    def _hex_to_rgb(h: str) -> tuple[int, int, int] | None:
        h = h.strip()
        if h.startswith("#"):
            h = h[1:]
        if len(h) != 6:
            return None
        try:
            r = int(h[0:2], 16)
            g = int(h[2:4], 16)
            b = int(h[4:6], 16)
            return (r, g, b)
        except Exception:
            return None

    bg = os.getenv("UI_BG")
    acc = os.getenv("UI_ACCENT")
    if bg:
        rgb = _hex_to_rgb(bg)
        if rgb:
            COLORS["bg"] = rgb
    if acc:
        rgb = _hex_to_rgb(acc)
        if rgb:
            COLORS["accent"] = rgb


_apply_env_overrides()
