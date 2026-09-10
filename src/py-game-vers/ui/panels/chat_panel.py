# ui/panels/chat_panel.py
"""
ChatPanel: chat history, input box, and tool invocation UI.

Responsibilities:
- Render a scrollable chat history area and a single-line input box
- Accept text input and submit via Enter
- If input starts with '/', treat as tool invocation and call services['tool'].invoke(name, args)
- Append messages to local history and optionally notify services['session']
- Keep UI code separate from domain logic; services handle persistence and AI

Usage:
    chat = ChatPanel(services)
    chat.handle_event(event)
    chat.update(dt)
    chat.render(surface, rect)
"""

from __future__ import annotations

import pygame
from ui.styles import COLORS, FONT, METRICS
from ui.widgets import ScrollList, TextInput

# Simple message tuple: (role, text)
Message = tuple[str, str]


class ChatPanel:
    def __init__(self, services: dict | None = None, history_limit: int = 200):
        self.services = services or {}
        self.history: list[Message] = []
        self.history_limit = history_limit

        # Text input with on_submit callback
        self.input = TextInput(
            placeholder="Type a message. Use /tool args to invoke tools.", on_submit=self._on_submit
        )
        # ScrollList to render messages; we provide a renderer function below
        self.scroll_list = ScrollList(items=self.history, renderer=self._render_message)
        # Cached layout rect for input and history rendering
        self._rect = (0, 0, 0, 0)

    # -------------------------
    # Public API
    # -------------------------
    def append_message(self, role: str, text: str) -> None:
        """Append a message to history and clamp length."""
        self.history.append((role, text))
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit :]
        # update scroll list items reference
        self.scroll_list.items = self.history

    # -------------------------
    # Input submit handling
    # -------------------------
    def _on_submit(self, text: str) -> None:
        """Called when the user presses Enter in the input box."""
        text = (text or "").strip()
        if not text:
            return
        # Append user's message
        self.append_message("You", text)

        # If text starts with '/', treat as tool invocation
        if text.startswith("/"):
            # parse: /toolName optional args...
            parts = text.lstrip("/").split(" ", 1)
            name = parts[0].strip()
            args = parts[1].strip() if len(parts) > 1 else ""
            tool_svc = self.services.get("tool")
            try:
                if tool_svc and hasattr(tool_svc, "invoke"):
                    # ToolService.invoke may return a string or (text, metadata)
                    resp = tool_svc.invoke(name, args)
                    # Normalize response to string for display
                    if isinstance(resp, tuple) and len(resp) >= 1:
                        display = resp[0]
                    else:
                        display = str(resp)
                    self.append_message("Tool", display)
                else:
                    self.append_message("System", f"No tool service available to run /{name}")
            except Exception as e:
                self.append_message("System", f"Tool error: {e}")
        else:
            # Normal chat message: notify session service and optionally tool service
            session_svc = self.services.get("session")
            try:
                if session_svc and hasattr(session_svc, "append"):
                    session_svc.append(text)
            except Exception:
                # swallow session errors but show a system message
                self.append_message("System", "Failed to append to session.")

            # Optionally echo a placeholder assistant response or call a conversation service
            # If a 'conversation' service exists, prefer it
            conv = self.services.get("conversation")
            if conv and hasattr(conv, "send"):
                try:
                    assistant_resp = conv.send(text)
                    if assistant_resp:
                        self.append_message("Assistant", str(assistant_resp))
                except Exception:
                    self.append_message("Assistant", "...")
            else:
                # placeholder assistant echo
                self.append_message("Assistant", "...")

        # Clear input after submit
        self.input.value = ""
        # Scroll to bottom
        self.scroll_list.scroll = 10**9  # large value; ScrollList will clamp

    # -------------------------
    # Event handling
    # -------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle events. The panel expects the scene to forward events to it.
        """
        # Let the input handle mouse/keyboard first (it manages focus)
        self.input.handle_event(event)
        # ScrollList handles mouse wheel and drag
        self.scroll_list.handle_event(event)

        # If Enter pressed and input is active, TextInput will call on_submit via handle_event
        # But some platforms may not route KEYDOWN to TextInput if it doesn't have focus.
        # We also support pressing Enter to submit when input is focused.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.input.active:
                # Simulate submit callback
                try:
                    self._on_submit(self.input.value)
                except Exception:
                    pass

    # -------------------------
    # Update
    # -------------------------
    def update(self, dt: float) -> None:
        self.input.update(dt)
        self.scroll_list.update(dt)

    # -------------------------
    # Rendering
    # -------------------------
    def _render_message(
        self, surface: pygame.Surface, item: Message, rect: tuple[int, int, int, int], index: int
    ) -> None:
        """
        Renderer used by ScrollList. Draws a single message into rect.
        """
        role, text = item
        x, y, w, h = rect
        pad = 8
        # background for alternating rows (subtle)
        if index % 2 == 0:
            bg = (24, 24, 30)
        else:
            bg = (22, 22, 28)
        pygame.draw.rect(surface, bg, (x, y, w, h))

        # role label
        role_color = COLORS["accent"] if role in ("Assistant", "Tool") else COLORS["muted"]
        role_surf = FONT["small"].render(f"{role}:", True, role_color)
        surface.blit(role_surf, (x + pad, y + pad))

        # message text (wrap if necessary)
        text_x = x + pad + role_surf.get_width() + 6
        max_w = w - (text_x - x) - pad
        # naive wrapping: split into words and build lines
        words = text.split(" ")
        line = ""
        line_y = y + pad
        for word in words:
            test = (line + " " + word).strip()
            test_surf = FONT["small"].render(test, True, COLORS["text"])
            if test_surf.get_width() <= max_w:
                line = test
            else:
                # render current line
                surf_line = FONT["small"].render(line, True, COLORS["text"])
                surface.blit(surf_line, (text_x, line_y))
                line_y += surf_line.get_height() + 2
                line = word
        # render last line
        if line:
            surf_line = FONT["small"].render(line, True, COLORS["text"])
            surface.blit(surf_line, (text_x, line_y))

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        """
        Render the chat panel into the provided rect: top area is history, bottom is input.
        """
        self._rect = rect
        x, y, w, h = rect
        pad = METRICS.get("panel_padding", 8)

        # background
        pygame.draw.rect(surface, COLORS.get("panel_bg", (28, 28, 36)), (x, y, w, h))

        # compute input area (fixed height)
        input_h = 36
        history_rect = (x + pad, y + pad, w - pad * 2, h - pad * 2 - input_h - pad)
        input_rect = (x + pad, y + h - pad - input_h, w - pad * 2, input_h)

        # Render history via ScrollList
        # ScrollList expects items and renderer; we already set that up
        self.scroll_list.render(surface, history_rect)

        # Render input box
        self.input.render(surface, input_rect)
