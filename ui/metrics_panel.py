"""Panel hiển thị metric tìm kiếm và tổng kết trận đấu."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from ai.base import GameAI
from config.settings import (
    ALGORITHM_LABELS,
    COLORS,
    MATCH_MODE_LABELS,
    GameSettings,
)
from game.board import PLAYER_X
from game.match_history import (
    MatchHistoryRecord,
    MoveMetricRecord,
    metric_record_for_view,
)
from game.state import GameState
from ui.components import draw_metric_card, draw_panel, draw_text
from utils.helpers import format_search_score, player_label


@dataclass(frozen=True)
class MetricsPanelContext:
    """Dữ liệu chỉ đọc cần thiết để render panel metric."""

    settings: GameSettings
    state: GameState
    review_index: int
    ai_players: dict[int, GameAI]
    move_metrics: dict[int, MoveMetricRecord]
    last_ai_player: int | None
    session_stats: dict[int, dict[str, int]]
    current_summary: MatchHistoryRecord | None
    is_ai_thinking: bool
    ai_error: str
    history_error: str
    game_seed: int


class MetricsPanel:
    """Tổng hợp và hiển thị metric mà không điều khiển trận đấu."""

    RECT = pygame.Rect(884, 90, 372, 620)

    @staticmethod
    def _depth_for_ai(settings: GameSettings, ai: GameAI) -> int:
        if ai.key == "minimax":
            return settings.minimax_depth
        if ai.key == "alphabeta":
            return settings.alphabeta_depth
        return 1

    @staticmethod
    def _metric_record(
        context: MetricsPanelContext,
    ) -> MoveMetricRecord | None:
        return metric_record_for_view(
            context.move_metrics,
            context.review_index,
            len(context.state.history),
        )

    @staticmethod
    def _metric_player(
        context: MetricsPanelContext,
        record: MoveMetricRecord | None,
    ) -> int | None:
        if record is not None:
            return record.player
        if context.state.current_player in context.ai_players:
            return context.state.current_player
        if context.last_ai_player is not None:
            return context.last_ai_player
        if context.ai_players:
            return next(iter(context.ai_players))
        return None

    def draw(
        self,
        surface: pygame.Surface,
        context: MetricsPanelContext,
    ) -> None:
        settings = context.settings
        state = context.state
        draw_panel(
            surface,
            self.RECT,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )
        draw_text(
            surface,
            "EVALUATION METRICS",
            18,
            COLORS["primary"],
            (906, 112),
            bold=True,
        )

        if context.review_index != len(state.history):
            status = "ĐANG XEM LẠI"
            status_color = COLORS["accent"]
        elif context.is_ai_thinking:
            status = "AI ĐANG TÍNH..."
            status_color = COLORS["accent"]
        elif state.game_over:
            status = "KẾT THÚC"
            status_color = COLORS["success"]
        else:
            status = f"LƯỢT {player_label(state.current_player)}"
            status_color = (
                COLORS["x"] if state.current_player == PLAYER_X else COLORS["o"]
            )
        draw_text(
            surface,
            status,
            15,
            status_color,
            (1232, 114),
            bold=True,
            anchor="topright",
        )

        record = self._metric_record(context)
        live_ai_turn = (
            context.review_index == len(state.history)
            and not state.game_over
            and state.current_player in context.ai_players
        )
        metric_player = (
            state.current_player
            if live_ai_turn
            else self._metric_player(context, record)
        )
        current_agent = context.ai_players.get(metric_player)
        metric = (
            record.metrics
            if record is not None and record.algorithm_key is not None
            else None
        )
        analysis = record.analysis if record is not None else None
        selected_candidate = analysis.selected if analysis is not None else None
        decision_note = (
            f"{analysis.score_label}: {format_search_score(selected_candidate.score)}"
            if analysis is not None and selected_candidate is not None
            else ""
        )
        node_note_parts = []
        if analysis is not None:
            node_note_parts.append(f"Candidates: {len(analysis.candidates)}")
        if metric is not None and metric.pruned_branches:
            node_note_parts.append(f"Pruned: {metric.pruned_branches:,}")
        node_note = " | ".join(node_note_parts)

        if live_ai_turn and current_agent is not None:
            current_ai = current_agent.name
            if current_agent.key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            else:
                depth_note = f"Depth: {self._depth_for_ai(settings, current_agent)}"
            move_note = "Current turn"
            if record is not None:
                move_note = (
                    f"Metric: Move {record.move_number} {player_label(record.player)}"
                )
        elif record is not None:
            current_ai = record.actor_name
            if record.algorithm_key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            elif record.algorithm_key is not None:
                depth_note = f"Depth: {record.depth}"
            else:
                depth_note = "Move by human"
            move_note = f"Move {record.move_number}: {player_label(record.player)}"
        else:
            current_ai = current_agent.name if current_agent else "Human"
            if current_agent is None:
                depth_note = ""
            elif current_agent.key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            else:
                depth_note = f"Depth: {self._depth_for_ai(settings, current_agent)}"
            move_note = "Current turn"

        if current_agent is None and record is None:
            depth_note = ""

        stats = (
            context.session_stats[metric_player]
            if metric_player in context.ai_players
            else {"wins": 0, "draws": 0, "losses": 0, "games": 0}
        )
        win_rate = (
            f"{stats['wins'] / stats['games'] * 100:.1f}%" if stats["games"] else "N/A"
        )
        if state.game_over and context.current_summary is not None:
            if context.current_summary.ai_move_count:
                total_value = f"{context.current_summary.average_time_ms:.2f} ms/move"
                total_note = context.current_summary.total_line
            else:
                total_value = f"{context.current_summary.move_count} moves"
                total_note = "Human match"
        else:
            total_value = "N/A"
            total_note = "Khi kết thúc"

        cards = [
            (
                "Execution Time",
                (
                    f"{metric.execution_time_ms:.2f} ms"
                    if metric is not None
                    else (
                        "Đang tính..."
                        if live_ai_turn and context.is_ai_thinking
                        else "N/A"
                    )
                ),
                COLORS["accent"],
                decision_note,
            ),
            (
                "Nodes Expanded",
                (
                    f"{metric.nodes_expanded:,}"
                    if metric is not None
                    else (
                        "Đang tính..."
                        if live_ai_turn and context.is_ai_thinking
                        else "N/A"
                    )
                ),
                COLORS["text"],
                node_note,
            ),
            ("Current AI", current_ai, COLORS["primary"], depth_note),
            (
                "Move Count",
                (
                    f"{context.review_index} / {len(state.history)}"
                    if context.review_index != len(state.history)
                    else str(len(state.history))
                ),
                COLORS["text"],
                move_note,
            ),
            (
                "Win Rate",
                win_rate,
                COLORS["success"],
                (
                    (f"W-D-L: {stats['wins']}-{stats['draws']}-{stats['losses']}")
                    if stats["games"]
                    else "Session"
                ),
            ),
            (
                "Game Total",
                total_value,
                COLORS["success"] if state.game_over else COLORS["muted"],
                total_note,
            ),
        ]
        y = 150
        for label, value, color, note in cards:
            draw_metric_card(
                surface,
                pygame.Rect(904, y, 332, 74),
                label,
                value,
                value_color=color,
                note=note,
            )
            y += 80

        draw_text(
            surface,
            f"Chế độ: {MATCH_MODE_LABELS[settings.match_mode]}",
            12,
            COLORS["muted"],
            (904, 623),
        )
        draw_text(
            surface,
            f"Điều kiện thắng: {settings.win_length} quân liên tiếp",
            12,
            COLORS["muted"],
            (904, 643),
        )
        if settings.match_mode == "ai_ai":
            matchup = (
                f"X: {ALGORITHM_LABELS[settings.ai_x]}  |  "
                f"O: {ALGORITHM_LABELS[settings.ai_o]}"
            )
            draw_text(
                surface,
                matchup,
                11,
                COLORS["muted"],
                (904, 663),
            )
        if context.ai_error or context.history_error:
            error = context.ai_error or context.history_error
            prefix = "AI error" if context.ai_error else "History error"
            draw_text(
                surface,
                f"{prefix}: {error[:32]}",
                11,
                COLORS["danger"],
                (904, 683),
            )
        else:
            draw_text(
                surface,
                f"Game seed: {context.game_seed:016X}",
                11,
                COLORS["muted"],
                (904, 683),
            )
