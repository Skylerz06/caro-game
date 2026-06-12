"""Màn hình duyệt lịch sử các trận đã lưu."""

from __future__ import annotations

import math

import pygame

from config.settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.match_history import MatchHistoryRecord
from ui.components import Button, IconButton, draw_gradient, draw_panel, draw_text


class HistoryScreen:
    """Hiển thị lịch sử persistent và mở replay từng trận."""

    PAGE_SIZE = 3
    PANEL = pygame.Rect(120, 130, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 180)

    def __init__(self) -> None:
        self.records: list[MatchHistoryRecord] = []
        self.page = 0
        self.back_button = Button(pygame.Rect(70, 36, 128, 46), "QUAY LẠI")
        self.prev_page_button = IconButton(pygame.Rect(1080, 40, 42, 42), "left")
        self.next_page_button = IconButton(pygame.Rect(1132, 40, 42, 42), "right")
        self.replay_buttons: list[tuple[Button, MatchHistoryRecord]] = []

    @property
    def page_count(self) -> int:
        return max(1, math.ceil(len(self.records) / self.PAGE_SIZE))

    def _page_records(self) -> list[MatchHistoryRecord]:
        start = self.page * self.PAGE_SIZE
        return self.records[start : start + self.PAGE_SIZE]

    def _rebuild_replay_buttons(self) -> None:
        self.replay_buttons = []
        for index, record in enumerate(self._page_records()):
            top = self.PANEL.top + 22 + index * 202
            button = Button(
                pygame.Rect(self.PANEL.right - 170, top + 48, 132, 36),
                "XEM LẠI",
                accent=True,
            )
            self.replay_buttons.append((button, record))

    def open(self, records: list[MatchHistoryRecord]) -> None:
        self.records = sorted(
            records,
            key=lambda record: record.number,
            reverse=True,
        )
        self.page = 0
        self._rebuild_replay_buttons()

    def handle_event(
        self, event: pygame.event.Event
    ) -> str | tuple[str, MatchHistoryRecord] | None:
        if self.back_button.handle_event(event):
            return "back"

        self.prev_page_button.enabled = self.page > 0
        self.next_page_button.enabled = self.page + 1 < self.page_count
        if self.prev_page_button.handle_event(event):
            self.page -= 1
            self._rebuild_replay_buttons()
            return None
        if self.next_page_button.handle_event(event):
            self.page += 1
            self._rebuild_replay_buttons()
            return None
        for button, record in self.replay_buttons:
            if button.handle_event(event):
                return "replay", record
        return None

    def update(self) -> None:
        self.prev_page_button.enabled = self.page > 0
        self.next_page_button.enabled = self.page + 1 < self.page_count

    def _draw_record(
        self,
        surface: pygame.Surface,
        record: MatchHistoryRecord,
        rect: pygame.Rect,
        replay_button: Button,
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
            (COLORS["success"] if "thắng" in record.result else COLORS["accent"]),
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
        replay_button.draw(surface)

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(surface, COLORS["background"], COLORS["background_2"])
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
            f"Đã lưu {len(self.records)} trận • Có thể xem lại từng nước",
            15,
            COLORS["muted"],
            (SCREEN_WIDTH // 2, 88),
            anchor="midtop",
        )
        self.prev_page_button.draw(surface)
        self.next_page_button.draw(surface)
        draw_text(
            surface,
            f"{self.page + 1}/{self.page_count}",
            13,
            COLORS["muted"],
            (1058, 61),
            anchor="midright",
        )

        draw_panel(
            surface,
            self.PANEL,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )
        if not self.records:
            draw_text(
                surface,
                "Chưa có trận đấu nào được lưu.",
                20,
                COLORS["muted"],
                self.PANEL.center,
                bold=True,
                anchor="center",
            )
            return

        for index, (button, record) in enumerate(self.replay_buttons):
            top = self.PANEL.top + 22 + index * 202
            self._draw_record(
                surface,
                record,
                pygame.Rect(
                    self.PANEL.left + 34,
                    top,
                    self.PANEL.width - 68,
                    188,
                ),
                button,
            )
