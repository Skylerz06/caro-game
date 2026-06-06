"""Màn hình menu chính."""

from __future__ import annotations

import pygame

from config.settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components import Button, draw_gradient, draw_panel, draw_text


class MenuScreen:
    def __init__(self) -> None:
        button_x = SCREEN_WIDTH // 2 - 170
        self.buttons = {
            "play": Button(
                pygame.Rect(button_x, 330, 340, 58),
                "PLAY",
                accent=True,
            ),
            "settings": Button(
                pygame.Rect(button_x, 404, 340, 58), "SETTINGS"
            ),
            "ai_settings": Button(
                pygame.Rect(button_x, 478, 340, 58),
                "AI MODE SELECTION",
            ),
            "exit": Button(
                pygame.Rect(button_x, 552, 340, 58),
                "EXIT",
                danger=True,
            ),
        }

    def handle_event(self, event: pygame.event.Event) -> str | None:
        for action, button in self.buttons.items():
            if button.handle_event(event):
                return action
        return None

    def update(self) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(
            surface, COLORS["background"], COLORS["background_2"]
        )

        # Họa tiết bàn cờ mờ tạo nhận diện mà không cần asset ngoài.
        grid_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        for x in range(-80, SCREEN_WIDTH + 80, 48):
            pygame.draw.line(
                grid_surface, (56, 189, 248, 13), (x, 0), (x + 300, 800)
            )
        for y in range(-80, SCREEN_HEIGHT + 80, 48):
            pygame.draw.line(
                grid_surface, (251, 146, 60, 10), (0, y), (1280, y - 250)
            )
        surface.blit(grid_surface, (0, 0))

        card = pygame.Rect(SCREEN_WIDTH // 2 - 245, 95, 490, 585)
        draw_panel(
            surface,
            card,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )

        draw_text(
            surface,
            "CARO",
            64,
            COLORS["text"],
            (SCREEN_WIDTH // 2, 145),
            bold=True,
            anchor="midtop",
        )
        draw_text(
            surface,
            "AI LAB",
            30,
            COLORS["primary"],
            (SCREEN_WIDTH // 2, 215),
            bold=True,
            anchor="midtop",
        )
        draw_text(
            surface,
            "Gomoku m,n,k  •  Greedy  •  Minimax  •  Alpha-Beta",
            14,
            COLORS["muted"],
            (SCREEN_WIDTH // 2, 264),
            anchor="midtop",
        )

        pygame.draw.line(
            surface,
            (57, 78, 110),
            (card.left + 55, 301),
            (card.right - 55, 301),
            1,
        )
        for button in self.buttons.values():
            button.draw(surface)

        draw_text(
            surface,
            "University AI Project  •  Pygame",
            13,
            COLORS["muted"],
            (SCREEN_WIDTH // 2, 648),
            anchor="center",
        )

