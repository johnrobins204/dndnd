# ui/window.py
"""
GameWindow: pygame application shell and scene stack.

Responsibilities:
- Initialize pygame and fonts
- Hold a reference to services (injected at construction)
- Manage a stack of Scene objects (push/pop)
- Run the main loop: poll events, forward to current scene, update, render, flip
- Provide a small API for scenes to request scene changes

Expectations:
- Scenes are objects with handle_event(event), update(dt), render(surface)
- services is a dict-like object containing at least:
    - 'tool': ToolService instance (optional)
    - 'session': SessionService instance (optional)
    - 'window': this GameWindow instance (set by constructor)
"""

import pygame

# Try to import window size from assets.config; fall back to defaults if missing.
try:
    from assets.config import WINDOW_HEIGHT, WINDOW_WIDTH
except Exception:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720


# Minimal logging helper
def _log(msg: str) -> None:
    # Replace with proper logger if desired
    print(f"[GameWindow] {msg}")


class GameWindow:
    """
    Main pygame application window and scene manager.

    Usage:
        services = { 'tool': tool_service, 'session': session_service }
        window = GameWindow(services)
        window.run()
    """

    def __init__(
        self,
        services: dict | None = None,
        width: int = WINDOW_WIDTH,
        height: int = WINDOW_HEIGHT,
        caption: str = "DnD DM Console",
    ):
        # Initialize pygame subsystems if not already initialized
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        self.width = width
        self.height = height
        self.caption = caption

        # Create display surface
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.caption)

        # Clock for framerate and dt
        self.clock = pygame.time.Clock()
        self.target_fps = 60

        # Services injected by the bootstrapper (app.main)
        self.services = services or {}
        # Make the window available to services and scenes
        self.services["window"] = self

        # Scene stack: last item is the active scene
        self._scene_stack: list[object] = []

        # Optional: a global UI scale factor for high-DPI or scaling
        self.ui_scale = 1.0

        # Input focus: which widget or scene currently receives keyboard input
        self.focus = None

        # Start with no scenes; caller should push initial scene (e.g., MainMenuScene)
        _log("Initialized GameWindow")

    # Scene stack management -------------------------------------------------
    def push_scene(self, scene) -> None:
        """Push a new scene onto the stack and call its on_enter if present."""
        self._scene_stack.append(scene)
        # If the scene expects services, ensure it's wired
        if hasattr(scene, "services"):
            scene.services = self.services
        if hasattr(scene, "on_enter"):
            try:
                scene.on_enter()
            except Exception as e:
                _log(f"Exception in scene.on_enter: {e}")

    def pop_scene(self) -> object | None:
        """Pop the current scene and call its on_exit if present."""
        if not self._scene_stack:
            return None
        scene = self._scene_stack.pop()
        if hasattr(scene, "on_exit"):
            try:
                scene.on_exit()
            except Exception as e:
                _log(f"Exception in scene.on_exit: {e}")
        return scene

    def replace_scene(self, scene) -> None:
        """Replace the current scene with a new one."""
        self.pop_scene()
        self.push_scene(scene)

    def clear_scenes(self) -> None:
        """Remove all scenes."""
        while self._scene_stack:
            self.pop_scene()

    @property
    def current_scene(self):
        """Return the active scene or None."""
        return self._scene_stack[-1] if self._scene_stack else None

    # Main loop -------------------------------------------------------------
    def run(self) -> None:
        """Run the main application loop until the window is closed."""
        running = True
        _log("Entering main loop")
        try:
            while running:
                # dt in seconds
                dt_ms = self.clock.tick(self.target_fps)
                dt = dt_ms / 1000.0

                # Event handling
                for event in pygame.event.get():
                    # Global quit handling
                    if event.type == pygame.QUIT:
                        running = False
                        break

                    # Allow scenes to handle events
                    scene = self.current_scene
                    if scene is not None:
                        try:
                            scene.handle_event(event)
                        except Exception as e:
                            _log(f"Exception in scene.handle_event: {e}")

                # Update
                scene = self.current_scene
                if scene is not None:
                    try:
                        scene.update(dt)
                    except Exception as e:
                        _log(f"Exception in scene.update: {e}")

                # Render
                # Clear screen (scenes are expected to draw full background)
                try:
                    if scene is not None:
                        scene.render(self.screen)
                    else:
                        # default background if no scene
                        self.screen.fill((18, 18, 18))
                except Exception as e:
                    _log(f"Exception in scene.render: {e}")
                    # Draw a fallback error message
                    self.screen.fill((40, 0, 0))
                    self._draw_error_overlay(str(e))

                # Flip buffers
                pygame.display.flip()

        except KeyboardInterrupt:
            _log("Interrupted by user")
        finally:
            _log("Shutting down pygame")
            pygame.quit()

    # Utilities -------------------------------------------------------------
    def set_focus(self, widget) -> None:
        """Set keyboard focus to a widget (panels/widgets can call this)."""
        self.focus = widget

    def get_size(self):
        return (self.width, self.height)

    def _draw_error_overlay(self, text: str) -> None:
        """Render a simple error overlay to the screen (used when scene.render fails)."""
        try:
            font = pygame.font.SysFont("Arial", 18)
            lines = text.splitlines()[:10]
            pad = 8
            x = pad
            y = pad
            bg = pygame.Surface((self.width - pad * 2, len(lines) * 22 + pad * 2))
            bg.set_alpha(220)
            bg.fill((0, 0, 0))
            self.screen.blit(bg, (pad, pad))
            for i, line in enumerate(lines):
                surf = font.render(line, True, (255, 100, 100))
                self.screen.blit(surf, (x + 6, y + 6 + i * 20))
        except Exception:
            # If even the overlay fails, there's nothing more we can do safely
            pass


# If this module is run directly, create a minimal window and a placeholder scene.
if __name__ == "__main__":
    # Minimal placeholder scene to demonstrate the window
    class _PlaceholderScene:
        def __init__(self, services=None):
            self.services = services or {}
            self.font = pygame.font.SysFont("Arial", 28)

        def handle_event(self, event):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # pop scene if window is available
                win = self.services.get("window")
                if win:
                    win.pop_scene()

        def update(self, dt):
            pass

        def render(self, surface):
            surface.fill((30, 30, 40))
            txt = self.font.render("Placeholder Scene - press ESC to pop", True, (220, 220, 220))
            surface.blit(txt, (40, 40))

    # Create a GameWindow and push the placeholder scene
    gw = GameWindow(services={})
    gw.push_scene(_PlaceholderScene(gw.services))
    gw.run()
