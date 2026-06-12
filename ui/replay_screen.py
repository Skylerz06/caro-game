"""Màn hình replay read-only cho một trận đã lưu."""

from __future__ import annotations

import pygame

from config.settings import COLORS, GameSettings
from game.board import PLAYER_O, PLAYER_X
from game.match_history import MatchHistoryRecord, metric_record_for_view
from game.state import GameState
from ui.board_view import BoardView
from ui.components import Button, IconButton, draw_gradient, draw_text
from ui.metrics_panel import MetricsPanel, MetricsPanelContext
from utils.helpers import player_label


class ReplayScreen:
    """Dựng lại bàn cờ từ JSON và cho phép duyệt từng nước."""

    HISTORY_PANEL = pygame.Rect(24, 724, 1232, 58)

    def __init__(self) -> None:
        self.record: MatchHistoryRecord | None = None
        self.settings = GameSettings()
        self.state = GameState(3, 3, 3)
        self.move_metrics = {}
        self.review_index = 0
        self.analysis_enabled = True
        self.back_button = Button(pygame.Rect(24, 18, 132, 44), "QUAY LẠI")
        self.prev_button = IconButton(pygame.Rect(558, 732, 42, 42), "left")
        self.next_button = IconButton(pygame.Rect(680, 732, 42, 42), "right")
        self.analysis_button = Button(
            pygame.Rect(984, 732, 198, 42), "PHÂN TÍCH: BẬT", accent=True
        )
        self.board_view = BoardView()
        self.metrics_panel = MetricsPanel()

    def open(self, record: MatchHistoryRecord) -> None:
        self.record = record
        self.settings = GameSettings.from_dict(
            {
                "rows": record.rows,
                "cols": record.cols,
                "win_length": record.win_length,
                "match_mode": record.match_mode,
                "ai_x": record.ai_x_key,
                "ai_o": record.ai_o_key,
            }
        )
        self.state = record.build_state()
        self.move_metrics = record.metrics_by_move
        self.review_index = len(self.state.history)
        self.analysis_enabled = True

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.back_button.handle_event(event):
            return "back"
        self.prev_button.enabled = self.review_index > 0
        self.next_button.enabled = self.review_index < len(self.state.history)
        if self.prev_button.handle_event(event):
            self.review_index -= 1
        elif self.next_button.handle_event(event):
            self.review_index += 1
        elif self.analysis_button.handle_event(event):
            self.analysis_enabled = not self.analysis_enabled
        return None

    def update(self) -> None:
        self.prev_button.enabled = self.review_index > 0
        self.next_button.enabled = self.review_index < len(self.state.history)

    def _draw_history(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface,
            COLORS["panel"],
            self.HISTORY_PANEL,
            border_radius=16,
        )
        draw_text(
            surface,
            "REPLAY HISTORY",
            12,
            COLORS["muted"],
            (42, 738),
            bold=True,
        )
        recent = self.state.history[max(0, self.review_index - 7) : self.review_index]
        history_text = "  ".join(
            f"{move.number}.{player_label(move.player)}:{move.notation}"
            for move in recent
        )
        draw_text(
            surface,
            history_text or "Trước nước đi đầu tiên",
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
            f"{self.review_index} / {len(self.state.history)}",
            15,
            COLORS["text"],
            (640, 753),
            bold=True,
            anchor="center",
        )
        draw_text(
            surface,
            "REPLAY",
            12,
            COLORS["accent"],
            (1234, 753),
            bold=True,
            anchor="midright",
        )

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(surface, COLORS["background"], COLORS["background_2"])
        self.back_button.draw(surface)
        if self.record is None:
            draw_text(
                surface,
                "Không có dữ liệu replay.",
                24,
                COLORS["muted"],
                surface.get_rect().center,
                anchor="center",
            )
            return

        draw_text(
            surface,
            f"REPLAY TRẬN #{self.record.number}",
            25,
            COLORS["text"],
            (178, 18),
            bold=True,
        )
        draw_text(
            surface,
            f"{self.record.timestamp}  •  {self.record.result}",
            13,
            COLORS["muted"],
            (180, 49),
        )

        analysis_record = metric_record_for_view(
            self.move_metrics,
            self.review_index,
            len(self.state.history),
        )
        self.board_view.draw(
            surface,
            self.state,
            self.settings,
            self.review_index,
            0,
            0,
            show_analysis=self.analysis_enabled,
            analysis=(
                analysis_record.analysis if analysis_record is not None else None
            ),
            show_result_notice=False,
        )
        self.metrics_panel.draw(
            surface,
            MetricsPanelContext(
                settings=self.settings,
                state=self.state,
                review_index=self.review_index,
                ai_players={},
                move_metrics=self.move_metrics,
                last_ai_player=None,
                session_stats={
                    PLAYER_X: {
                        "wins": 0,
                        "draws": 0,
                        "losses": 0,
                        "games": 0,
                    },
                    PLAYER_O: {
                        "wins": 0,
                        "draws": 0,
                        "losses": 0,
                        "games": 0,
                    },
                },
                current_summary=self.record,
                is_ai_thinking=False,
                ai_error="",
                history_error="",
                game_seed=self.record.game_seed,
            ),
        )
        self._draw_history(surface)
