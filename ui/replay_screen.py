"""Màn hình replay read-only cho một trận đã lưu."""

from __future__ import annotations

import pygame

from config.settings import COLORS, GameSettings
from game.match_history import MatchHistoryRecord, metric_record_for_view
from game.metrics import new_session_stats
from game.state import GameState
from ui.board_view import BoardView
from ui.components import Button, draw_gradient, draw_text
from ui.metrics_panel import MetricsPanel, MetricsPanelContext
from ui.move_history_bar import MoveHistoryBar


class ReplayScreen:
    """Dựng lại bàn cờ từ JSON và cho phép duyệt từng nước."""

    def __init__(self) -> None:
        self.record: MatchHistoryRecord | None = None
        self.settings = GameSettings()
        self.state = GameState(3, 3, 3)
        self.move_metrics = {}
        self.history_bar = MoveHistoryBar(analysis_enabled=True)
        self.back_button = Button(pygame.Rect(24, 18, 132, 44), "QUAY LẠI")
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
        self.history_bar.reset(len(self.state.history), analysis_enabled=True)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.back_button.handle_event(event):
            return "back"
        self.history_bar.handle_event(event, len(self.state.history))
        return None

    def update(self) -> None:
        self.history_bar.sync(len(self.state.history))

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
            self.history_bar.review_index,
            len(self.state.history),
        )
        self.board_view.draw(
            surface,
            self.state,
            self.settings,
            self.history_bar.review_index,
            0,
            0,
            show_analysis=self.history_bar.analysis_enabled,
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
                review_index=self.history_bar.review_index,
                ai_players={},
                move_metrics=self.move_metrics,
                last_ai_player=None,
                session_stats=new_session_stats(),
                current_summary=self.record,
                is_ai_thinking=False,
                ai_error="",
                history_error="",
                game_seed=self.record.game_seed,
            ),
        )
        self.history_bar.draw(
            surface,
            self.state.history,
            title="REPLAY HISTORY",
            empty_text="Trước nước đi đầu tiên",
            mode_text="REPLAY",
            mode_color=COLORS["accent"],
        )
