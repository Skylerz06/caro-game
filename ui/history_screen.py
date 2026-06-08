"""Màn hình xem lịch sử các ván đã kết thúc trong phiên chạy."""

from __future__ import annotations

import pygame

from config.settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.match_history import MatchHistoryRecord
from ui.components import Button, draw_gradient, draw_panel, draw_text


class HistoryScreen:
    """Hiển thị tổng kết trận để người dùng xem lại sau khi rời bàn cờ."""

    def __init__(self) -> None:
        self.records: list[MatchHistoryRecord] = []
        self.back_button = Button(
            pygame.Rect(70, 36, 128, 46), "QUAY LẠI"
        )

    def open(self, records: list[MatchHistoryRecord]) -> None:
        self.records = list(records)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.back_button.handle_event(event):
            return "back"
        return None

    def update(self) -> None:
        return None

    def _draw_record(
        self,
        surface: pygame.Surface,
        record: MatchHistoryRecord,
        rect: pygame.Rect,
    ) -> None:
        draw_panel(
            surface,
            rect,
            COLORS["panel_light"],
            radius=14,
            border_color=(57, 78, 110),
            shadow=False,
        )
        draw_text(
            surface,
            f"#{record.number}  {record.timestamp}",
            15,
            COLORS["muted"],
            (rect.left + 18, rect.top + 14),
            bold=True,
        )
        draw_text(
            surface,
            record.result.upper(),
            18,
            (
                COLORS["success"]
                if "thắng" in record.result
                else COLORS["accent"]
            ),
            (rect.right - 18, rect.top + 12),
            bold=True,
            anchor="topright",
        )
        draw_text(
            surface,
            f"{record.mode_label} | {record.board_label}",
            14,
            COLORS["text"],
            (rect.left + 18, rect.top + 44),
        )
        draw_text(
            surface,
            f"X: {record.x_agent} | O: {record.o_agent}",
            13,
            COLORS["muted"],
            (rect.left + 18, rect.top + 72),
        )
        draw_text(
            surface,
            f"Moves: {record.move_count}",
            13,
            COLORS["muted"],
            (rect.left + 18, rect.top + 100),
        )
        draw_text(
            surface,
            f"Total: {record.total_line}",
            13,
            COLORS["muted"],
            (rect.left + 18, rect.top + 124),
        )
        draw_text(
            surface,
            f"Average: {record.average_line}",
            12,
            COLORS["muted"],
            (rect.left + 18, rect.top + 148),
        )
        draw_text(
            surface,
            f"Seed: {record.game_seed:016X}",
            12,
            COLORS["muted"],
            (rect.left + 18, rect.top + 170),
        )

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(
            surface, COLORS["background"], COLORS["background_2"]
        )
        self.back_button.draw(surface)
        draw_text(
            surface,
            "LỊCH SỬ ĐẤU",
            36,
            COLORS["text"],
            (SCREEN_WIDTH // 2, 40),
            bold=True,
            anchor="midtop",
        )
        draw_text(
            surface,
            "Các ván đã kết thúc trong phiên chạy hiện tại",
            15,
            COLORS["muted"],
            (SCREEN_WIDTH // 2, 88),
            anchor="midtop",
        )

        panel = pygame.Rect(120, 130, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 180)
        draw_panel(
            surface,
            panel,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )

        if not self.records:
            draw_text(
                surface,
                "Chưa có trận đấu nào kết thúc.",
                20,
                COLORS["muted"],
                panel.center,
                bold=True,
                anchor="center",
            )
            return

        recent = list(reversed(self.records[-3:]))
        for index, record in enumerate(recent):
            top = panel.top + 22 + index * 202
            self._draw_record(
                surface,
                record,
                pygame.Rect(panel.left + 34, top, panel.width - 68, 188),
            )
