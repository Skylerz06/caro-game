"""Thanh điều hướng move history dùng chung cho game và replay."""

from __future__ import annotations

import pygame

from config.settings import COLORS
from game.state import Move
from ui.components import Button, IconButton, draw_text
from utils.helpers import player_label


class MoveHistoryBar:
    """Quản lý review index, nút điều hướng và toggle phân tích AI."""

    PANEL_RECT = pygame.Rect(24, 724, 1232, 58)

    def __init__(self, *, analysis_enabled: bool = False) -> None:
        self.review_index = 0
        self.analysis_enabled = analysis_enabled
        self.prev_button = IconButton(pygame.Rect(558, 732, 42, 42), "left")
        self.next_button = IconButton(pygame.Rect(680, 732, 42, 42), "right")
        self.analysis_button = Button(
            pygame.Rect(984, 732, 198, 42),
            "PHÂN TÍCH AI",
            accent=analysis_enabled,
        )

    def reset(self, review_index: int, *, analysis_enabled: bool | None = None) -> None:
        self.review_index = max(0, review_index)
        if analysis_enabled is not None:
            self.analysis_enabled = analysis_enabled
        self.sync(review_index)

    def sync(self, history_length: int) -> None:
        self.review_index = min(self.review_index, history_length)
        self.prev_button.enabled = self.review_index > 0
        self.next_button.enabled = self.review_index < history_length

    def handle_event(self, event: pygame.event.Event, history_length: int) -> bool:
        self.sync(history_length)
        for button, delta in ((self.prev_button, -1), (self.next_button, 1)):
            if button.handle_event(event):
                self.review_index += delta
                self.sync(history_length)
                return True
        if self.analysis_button.handle_event(event):
            self.analysis_enabled = not self.analysis_enabled
            return True
        return False

    def move_to_latest(self, history_length: int) -> None:
        self.review_index = history_length
        self.sync(history_length)

    def draw(
        self,
        surface: pygame.Surface,
        history: list[Move],
        *,
        title: str,
        empty_text: str,
        mode_text: str,
        mode_color: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(surface, COLORS["panel"], self.PANEL_RECT, border_radius=16)
        draw_text(
            surface,
            title,
            12,
            COLORS["muted"],
            (42, 738),
            bold=True,
        )
        recent = history[max(0, self.review_index - 7) : self.review_index]
        history_text = "  ".join(
            f"{move.number}.{player_label(move.player)}:{move.notation}"
            for move in recent
        )
        draw_text(
            surface,
            history_text or empty_text,
            14,
            COLORS["text"],
            (160, 737),
        )

        self.prev_button.draw(surface)
        self.next_button.draw(surface)
        self.analysis_button.text = (
            "PHÂN TÍCH: BẬT" if self.analysis_enabled else "PHÂN TÍCH AI"
        )
        self.analysis_button.accent = self.analysis_enabled
        self.analysis_button.draw(surface)
        draw_text(
            surface,
            f"{self.review_index} / {len(history)}",
            15,
            COLORS["text"],
            (640, 753),
            bold=True,
            anchor="center",
        )
        draw_text(
            surface,
            mode_text,
            12,
            mode_color,
            (1234, 753),
            bold=True,
            anchor="midright",
        )
