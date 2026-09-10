# ui/scenes.py
"""
Scene implementations for the pygame DnD DM UI.

Provides:
- Scene (base class)
- MainMenuScene
- GameScene
- CharacterEditorScene
- QuestScene

Scenes are lightweight controllers that compose panels and widgets.
They receive an injected `services` dict (from GameWindow) and must
not call persistence or AI directly; instead they call services.
"""

import pygame

from ui.panels.character_panel import CharacterPanel
from ui.panels.chat_panel import ChatPanel
from ui.panels.quest_panel import QuestPanel
from ui.panels.table_panel import TablePanel
from ui.styles import COLORS, FONT
from ui.widgets import Button, Label


class Scene:
    """Base scene. Scenes should override handle_event, update, render."""

    def __init__(self, services: dict | None = None):
        self.services = services or {}

    def on_enter(self) -> None:
        """Called when the scene becomes active (pushed)."""
        pass

    def on_exit(self) -> None:
        """Called when the scene is popped or replaced."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a single pygame event."""
        pass

    def update(self, dt: float) -> None:
        """Update scene state (dt seconds since last frame)."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Render the scene to the provided surface."""
        surface.fill(COLORS["bg"])


# ---------------------------------------------------------------------------
# Main menu scene
# ---------------------------------------------------------------------------
class MainMenuScene(Scene):
    def __init__(self, services: dict | None = None):
        super().__init__(services)
        self.title = Label("DnD DM Console", FONT["large"], COLORS["accent"])
        self.start_button = Button("Start Game", callback=self._on_start)
        self.quit_button = Button("Quit", callback=self._on_quit)
        # small layout state
        self._hovered = None

    def _on_start(self):
        # Push GameScene onto the window's scene stack
        win = self.services.get("window")
        if win:
            win.push_scene(GameScene(self.services))

    def _on_quit(self):
        # Request window to quit by postingac a QUIT event
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_event(self, event: pygame.event.Event) -> None:
        # Forward mouse events to buttons
        self.start_button.handle_event(event)
        self.quit_button.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["menu_bg"])
        w, h = surface.get_size()
        # Title
        self.title.render(surface, (w // 2 - 220, 60, 440, 60))
        # Buttons
        btn_w, btn_h = 220, 56
        self.start_button.render(surface, (w // 2 - btn_w // 2, 180, btn_w, btn_h))
        self.quit_button.render(surface, (w // 2 - btn_w // 2, 260, btn_w, btn_h))


# ---------------------------------------------------------------------------
# Game scene (main tabletop view)
# ---------------------------------------------------------------------------
class GameScene(Scene):
    def __init__(self, services: dict | None = None):
        super().__init__(services)
        # Panels
        self.table = TablePanel()
        self.chat = ChatPanel(self.services)
        self.characters = CharacterPanel(self.services)
        self.quest = QuestPanel(self.services)
        # Top bar quick actions
        self.top_save = Button("Save", callback=self._on_save)
        self.top_back = Button("Back", callback=self._on_back)
        # small state
        self._last_resize = None

    def on_enter(self) -> None:
        # Called when scene becomes active; could load session state here
        session = self.services.get("session")
        if session and hasattr(session, "ensure_active"):
            try:
                session.ensure_active()
            except Exception:
                pass

    def _on_save(self):
        svc = self.services.get("game")
        if svc and hasattr(svc, "save"):
            try:
                svc.save()
            except Exception:
                pass

    def _on_back(self):
        win = self.services.get("window")
        if win:
            win.pop_scene()

    def handle_event(self, event: pygame.event.Event) -> None:
        # Route events to panels; panels decide whether to consume them
        # Panels are responsible for their own hit testing
        self.table.handle_event(event)
        self.chat.handle_event(event)
        self.characters.handle_event(event)
        self.quest.handle_event(event)

        # Top bar buttons
        self.top_save.handle_event(event)
        self.top_back.handle_event(event)

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # quick back to main menu
                win = self.services.get("window")
                if win:
                    win.pop_scene()
            elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                # open character editor for first character (example)
                win = self.services.get("window")
                if win:
                    win.push_scene(CharacterEditorScene(self.services, character_index=0))

    def update(self, dt: float) -> None:
        self.table.update(dt)
        self.chat.update(dt)
        self.characters.update(dt)
        self.quest.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(COLORS["game_bg"])
        w, h = surface.get_size()
        left_w = int(w * 0.65)
        right_w = w - left_w

        # Table panel (left)
        self.table.render(surface, (0, 0, left_w, h))

        # Right column layout
        # Characters (top)
        char_h = int(h * 0.35)
        self.characters.render(surface, (left_w, 0, right_w, char_h))

        # Quest (middle)
        quest_h = int(h * 0.20)
        self.quest.render(surface, (left_w, char_h, right_w, quest_h))

        # Chat (bottom)
        chat_h = h - char_h - quest_h
        self.chat.render(surface, (left_w, char_h + quest_h, right_w, chat_h))

        # Top bar overlay
        bar_h = 48
        pygame.draw.rect(surface, (18, 18, 22), (0, 0, w, bar_h))
        # Title
        title_surf = FONT["normal"].render("Campaign: Demo Campaign", True, COLORS["text"])
        surface.blit(title_surf, (12, 12))
        # Buttons
        self.top_save.render(surface, (w - 220, 6, 80, 36))
        self.top_back.render(surface, (w - 120, 6, 80, 36))


# ---------------------------------------------------------------------------
# Character editor scene
# ---------------------------------------------------------------------------
class CharacterEditorScene(Scene):
    def __init__(self, services: dict | None = None, character_index: int = 0):
        super().__init__(services)
        self.character_index = character_index
        self.font = FONT["normal"]
        self._load_character()

        # simple UI controls
        self.save_button = Button("Save", callback=self._on_save)
        self.cancel_button = Button("Cancel", callback=self._on_cancel)

    def _load_character(self):
        # Load character data from service or use placeholder
        repo = self.services.get("character_repo")
        if repo and hasattr(repo, "list"):
            try:
                chars = repo.list()
                if 0 <= self.character_index < len(chars):
                    self.character = chars[self.character_index]
                    return
            except Exception:
                pass
        # fallback placeholder
        self.character = {"name": "Unnamed", "class": "None", "level": 1, "hp": "0/0", "notes": ""}

    def _on_save(self):
        repo = self.services.get("character_repo")
        if repo and hasattr(repo, "update"):
            try:
                repo.update(self.character)
            except Exception:
                pass
        win = self.services.get("window")
        if win:
            win.pop_scene()

    def _on_cancel(self):
        win = self.services.get("window")
        if win:
            win.pop_scene()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.save_button.handle_event(event)
        self.cancel_button.handle_event(event)
        # Basic text editing could be added here

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((28, 28, 34))
        w, h = surface.get_size()
        box_w = min(800, w - 80)
        box_h = min(480, h - 120)
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2
        pygame.draw.rect(surface, (22, 22, 28), (box_x, box_y, box_w, box_h), border_radius=8)
        # Character fields
        name_s = self.font.render(f"Name: {self.character.get('name')}", True, COLORS["text"])
        class_s = self.font.render(f"Class: {self.character.get('class')}", True, COLORS["text"])
        level_s = self.font.render(f"Level: {self.character.get('level')}", True, COLORS["text"])
        hp_s = self.font.render(f"HP: {self.character.get('hp')}", True, COLORS["text"])
        surface.blit(name_s, (box_x + 20, box_y + 20))
        surface.blit(class_s, (box_x + 20, box_y + 60))
        surface.blit(level_s, (box_x + 20, box_y + 100))
        surface.blit(hp_s, (box_x + 20, box_y + 140))
        # Buttons
        self.save_button.render(surface, (box_x + box_w - 200, box_y + box_h - 60, 80, 36))
        self.cancel_button.render(surface, (box_x + box_w - 100, box_y + box_h - 60, 80, 36))


# ---------------------------------------------------------------------------
# Quest scene (full-screen quest editor/viewer)
# ---------------------------------------------------------------------------
class QuestScene(Scene):
    def __init__(self, services: dict | None = None, quest_id: int | None = None):
        super().__init__(services)
        self.quest_id = quest_id
        self.font = FONT["normal"]
        self._load_quest()

    def _load_quest(self):
        repo = self.services.get("quest_repo")
        if repo and hasattr(repo, "get"):
            try:
                self.quest = (
                    repo.get(self.quest_id)
                    if self.quest_id is not None
                    else {"title": "No quest", "goal": "", "objectives": []}
                )
                return
            except Exception:
                pass
        self.quest = {
            "title": "No quest",
            "goal": "No active quest",
            "objectives": ["Example objective"],
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        # Escape to go back
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            win = self.services.get("window")
            if win:
                win.pop_scene()

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((26, 26, 32))
        w, h = surface.get_size()
        title = self.font.render(self.quest.get("title", "Quest"), True, COLORS["accent"])
        goal = self.font.render(self.quest.get("goal", ""), True, COLORS["text"])
        surface.blit(title, (24, 24))
        surface.blit(goal, (24, 64))
        for i, obj in enumerate(self.quest.get("objectives", [])):
            obj_s = self.font.render(f"{i + 1}. {obj}", True, COLORS["text"])
            surface.blit(obj_s, (36, 110 + i * 28))
