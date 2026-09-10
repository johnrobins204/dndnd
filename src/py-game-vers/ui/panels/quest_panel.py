# ui/panels/quest_panel.py
"""
QuestPanel: displays current quest summary, objectives, and step navigation.

Responsibilities:
- Load quest data from services (quest_repo) if available, otherwise use sample data
- Render quest title, goal, objectives, and simple progress UI
- Allow advancing/retreating steps and opening the full QuestScene for editing/viewing
- Keep UI-only state (selected objective index) and call services for persistence/actions
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from ui.scenes import QuestScene  # type: ignore

from ui.styles import COLORS, FONT, METRICS
from ui.widgets import Button


class QuestPanel:
    def __init__(self, services: dict | None = None):
        self.services = services or {}
        self._load_quest_from_service()
        self.selected_objective: int | None = None

        self.btn_prev = Button("Prev", callback=self._on_prev)
        self.btn_next = Button("Next", callback=self._on_next)
        self.btn_open = Button("Open", callback=self._on_open)

    def _load_quest_from_service(self) -> None:
        repo = self.services.get("quest_repo")
        try:
            if repo and hasattr(repo, "get_active"):
                q = repo.get_active()
                if q:
                    self.quest = q
                    return
            if repo and hasattr(repo, "list"):
                all_q = repo.list()
                if all_q:
                    self.quest = all_q[0]
                    return
        except Exception:
            pass

        self.quest = {
            "id": None,
            "title": "The Missing Heirloom",
            "goal": "Recover the family heirloom stolen from the manor.",
            "objectives": [
                {"text": "Investigate the manor grounds", "done": False},
                {"text": "Question the suspicious merchant", "done": False},
                {"text": "Find the hidden cellar", "done": False},
                {"text": "Confront the thief", "done": False},
            ],
            "current_step": 0,
        }

    def _on_prev(self) -> None:
        cur = self.quest.get("current_step", 0)
        if cur > 0:
            self.quest["current_step"] = cur - 1
            self.selected_objective = cur - 1
            repo = self.services.get("quest_repo")
            try:
                if repo and hasattr(repo, "save"):
                    repo.save(self.quest)
            except Exception:
                pass

    def _on_next(self) -> None:
        cur = self.quest.get("current_step", 0)
        if cur < len(self.quest.get("objectives", [])) - 1:
            self.quest["current_step"] = cur + 1
            self.selected_objective = cur + 1
            repo = self.services.get("quest_repo")
            try:
                if repo and hasattr(repo, "save"):
                    repo.save(self.quest)
            except Exception:
                pass

    def _on_open(self) -> None:
        win = self.services.get("window")
        if not win:
            return

        # Local import avoids circular import with ui.scenes
        from ui.scenes import QuestScene

        win.push_scene(QuestScene(self.services, quest_id=self.quest.get("id")))

    def refresh(self) -> None:
        self._load_quest_from_service()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.btn_prev.handle_event(event)
        self.btn_next.handle_event(event)
        self.btn_open.handle_event(event)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if hasattr(self, "_last_rect"):
                rx, ry, rw, rh = self._last_rect
                mx, my = event.pos
                if not (rx <= mx <= rx + rw and ry <= my <= ry + rh):
                    return

                pad = METRICS.get("panel_padding", 8)
                title_h = FONT["normal"].get_height()
                goal_h = FONT["small"].get_height()
                y_start = ry + pad + title_h + pad + goal_h + pad
                obj_h = FONT["small"].get_height() + 8

                rel_y = my - y_start
                if rel_y >= 0:
                    idx = int(rel_y // (obj_h + 6))
                    if 0 <= idx < len(self.quest.get("objectives", [])):
                        obj = self.quest["objectives"][idx]
                        obj["done"] = not bool(obj.get("done"))

                        repo = self.services.get("quest_repo")
                        try:
                            if repo and hasattr(repo, "save"):
                                repo.save(self.quest)
                        except Exception:
                            pass

                        self.selected_objective = idx

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
        self._last_rect = rect
        x, y, w, h = rect
        pad = METRICS.get("panel_padding", 8)

        pygame.draw.rect(surface, COLORS.get("panel_bg", (28, 28, 36)), (x, y, w, h))

        title = self.quest.get("title", "No quest")
        title_surf = FONT["normal"].render(title, True, COLORS["accent"])
        surface.blit(title_surf, (x + pad, y + pad))

        goal = self.quest.get("goal", "")
        goal_surf = FONT["small"].render(goal, True, COLORS["text"])
        surface.blit(goal_surf, (x + pad, y + pad + title_surf.get_height() + 6))

        objs = self.quest.get("objectives", [])
        obj_y = y + pad + title_surf.get_height() + 6 + goal_surf.get_height() + pad
        obj_h = FONT["small"].get_height() + 8

        for i, obj in enumerate(objs):
            done = bool(obj.get("done"))
            text = obj.get("text", "")

            box_size = 16
            bx = x + pad
            by = obj_y + i * (obj_h + 6)
            box_rect = pygame.Rect(bx, by, box_size, box_size)

            pygame.draw.rect(surface, (40, 40, 48), box_rect, border_radius=3)

            if done:
                pygame.draw.line(surface, COLORS["accent"], (bx + 3, by + box_size // 2),
                                 (bx + box_size // 2, by + box_size - 4), 2)
                pygame.draw.line(surface, COLORS["accent"], (bx + box_size // 2, by + box_size - 4),
                                 (bx + box_size - 3, by + 3), 2)

            txt_x = bx + box_size + 8
            txt_y = by
            color = COLORS["muted"] if done else COLORS["text"]
            txt_surf = FONT["small"].render(text, True, color)
            surface.blit(txt_surf, (txt_x, txt_y))

            cur = self.quest.get("current_step", 0)
            if i == cur:
                pygame.draw.rect(surface, COLORS["accent"], (x + 2, by, 4, box_size))

        btn_w = 64
        btn_h = 28
        gap = 8
        bx = x + pad
        by = y + h - pad - btn_h

        self.btn_prev.render(surface, (bx, by, btn_w, btn_h))
        self.btn_next.render(surface, (bx + btn_w + gap, by, btn_w, btn_h))
        self.btn_open.render(surface, (x + w - pad - btn_w, by, btn_w, btn_h))
