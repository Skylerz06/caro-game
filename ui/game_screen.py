"""Màn hình thi đấu, metrics và xem lại lịch sử."""

from __future__ import annotations

from datetime import datetime
from queue import Empty, Queue
from threading import Thread

import pygame

from ai import create_ai
from ai.base import GameAI
from config.settings import COLORS, MATCH_MODE_LABELS, GameSettings
from game.board import Board, PLAYER_O, PLAYER_X
from game.history_store import MatchHistoryStore
from game.match_history import (
    MatchHistoryRecord,
    MoveMetricRecord,
    metric_record_for_view,
    next_match_number,
)
from game.state import GameState
from ui.board_view import BoardView
from ui.components import Button, IconButton, draw_gradient, draw_panel, draw_text
from ui.metrics_panel import MetricsPanel, MetricsPanelContext
from utils.helpers import SearchMetrics, player_label
from utils.seedmaker import derive_seed, new_global_seed


class GameScreen:
    BOARD_PANEL = BoardView.PANEL_RECT
    BOARD_AREA = BoardView.AREA_RECT
    SIDE_PANEL = MetricsPanel.RECT
    HISTORY_PANEL = pygame.Rect(24, 724, 1232, 58)
    RESULT_NOTICE_MS = 5000

    def __init__(
        self,
        settings: GameSettings,
        match_history: list[MatchHistoryRecord] | None = None,
        history_store: MatchHistoryStore | None = None,
    ) -> None:
        self.settings = settings
        self.history_store = history_store
        self.board_view = BoardView()
        self.metrics_panel = MetricsPanel()
        self.state = GameState(settings.rows, settings.cols, settings.win_length)
        self.ai_players: dict[int, GameAI] = {}
        self.last_metrics = SearchMetrics()
        self.last_ai_player: int | None = None
        self.review_index = 0
        self.last_action_time = pygame.time.get_ticks()
        self.result_recorded = False
        self.search_generation = 0
        self.ai_search_thread: Thread | None = None
        self.ai_results: Queue = Queue()
        self.ai_error = ""
        self.game_seed = 0
        self.move_metrics: dict[int, MoveMetricRecord] = {}
        self.current_summary: MatchHistoryRecord | None = None
        self.match_history = match_history if match_history is not None else []
        self.history_error = ""
        self.game_total_time_ms = 0.0
        self.game_total_nodes = 0
        self.game_total_pruned = 0
        self.game_ai_moves = 0
        self.result_notice_started_at = 0
        self.analysis_enabled = False
        self.session_stats = {
            PLAYER_X: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
            PLAYER_O: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
        }

        self.menu_button = Button(pygame.Rect(24, 18, 116, 44), "MENU")
        self.student_panel = pygame.Rect(310, 18, 570, 44)
        self.restart_button = Button(pygame.Rect(1038, 18, 142, 44), "CHƠI LẠI")
        self.history_button = Button(pygame.Rect(902, 18, 124, 44), "LỊCH SỬ")
        self.settings_button = IconButton(
            pygame.Rect(1192, 16, 48, 48), "gear", tooltip="Cài đặt"
        )
        self.prev_button = IconButton(pygame.Rect(558, 732, 42, 42), "left")
        self.next_button = IconButton(pygame.Rect(680, 732, 42, 42), "right")
        self.analysis_button = Button(pygame.Rect(984, 732, 198, 42), "PHÂN TÍCH AI")
        self.start(settings)

    def start(self, settings: GameSettings, reset_session: bool = True) -> None:
        self._invalidate_search()
        self.settings = GameSettings.from_dict(settings.to_dict())
        self.state = GameState(
            self.settings.rows,
            self.settings.cols,
            self.settings.win_length,
        )
        self._create_ai_players()

        self.last_metrics = SearchMetrics()
        self.last_ai_player = None
        self.review_index = 0
        self.last_action_time = pygame.time.get_ticks()
        self.result_recorded = False
        self.ai_error = ""
        self.history_error = ""
        self.move_metrics = {}
        self.current_summary = None
        self.game_total_time_ms = 0.0
        self.game_total_nodes = 0
        self.game_total_pruned = 0
        self.game_ai_moves = 0
        self.result_notice_started_at = 0
        if reset_session:
            self.session_stats = {
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
            }

    def _restart(self) -> None:
        self._invalidate_search()
        self.state.reset()
        self._create_ai_players()
        self.last_metrics = SearchMetrics()
        self.last_ai_player = None
        self.review_index = 0
        self.last_action_time = pygame.time.get_ticks()
        self.result_recorded = False
        self.ai_error = ""
        self.history_error = ""
        self.move_metrics = {}
        self.current_summary = None
        self.game_total_time_ms = 0.0
        self.game_total_nodes = 0
        self.game_total_pruned = 0
        self.game_ai_moves = 0
        self.result_notice_started_at = 0

    def _create_ai_players(self) -> None:
        """Mỗi ván có global seed mới, sau đó tách seed cho từng AI."""
        self.game_seed = new_global_seed()
        self.ai_players = {}
        if self.settings.match_mode == "human_ai":
            self.ai_players[PLAYER_O] = create_ai(
                self.settings.ai_o,
                seed=derive_seed(self.game_seed, "ai:o"),
            )
        elif self.settings.match_mode == "ai_ai":
            self.ai_players[PLAYER_X] = create_ai(
                self.settings.ai_x,
                seed=derive_seed(self.game_seed, "ai:x"),
            )
            self.ai_players[PLAYER_O] = create_ai(
                self.settings.ai_o,
                seed=derive_seed(self.game_seed, "ai:o"),
            )

    def _invalidate_search(self) -> None:
        """Làm kết quả đang tính trở nên vô hiệu khi đổi/reset ván."""
        self.search_generation += 1
        while True:
            try:
                self.ai_results.get_nowait()
            except Empty:
                break
        if self.ai_search_thread is not None and not self.ai_search_thread.is_alive():
            self.ai_search_thread = None

    @property
    def is_ai_thinking(self) -> bool:
        return bool(
            self.ai_search_thread is not None and self.ai_search_thread.is_alive()
        )

    def _is_human_turn(self) -> bool:
        return self.state.current_player not in self.ai_players

    def _depth_for_ai(self, ai: GameAI) -> int:
        """Depth phụ thuộc thuật toán, không dùng một global depth."""
        if ai.key == "minimax":
            return self.settings.minimax_depth
        if ai.key == "alphabeta":
            return self.settings.alphabeta_depth
        return 1

    def _handle_board_click(self, position: tuple[int, int]) -> None:
        if (
            self.state.game_over
            or not self._is_human_turn()
            or self.review_index != len(self.state.history)
        ):
            return

        cell = self.board_view.cell_at(position, self.settings)
        if cell is None:
            return

        row, col = cell
        player = self.state.current_player
        if self.state.play_move(row, col):
            self.move_metrics[len(self.state.history)] = MoveMetricRecord(
                move_number=len(self.state.history),
                player=player,
                actor_name="Human",
                algorithm_key=None,
                depth=0,
                metrics=SearchMetrics(),
            )
            self.review_index = len(self.state.history)
            self.last_action_time = pygame.time.get_ticks()
            self._record_result_if_needed()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.menu_button.handle_event(event):
            self._invalidate_search()
            return "menu"
        if self.restart_button.handle_event(event):
            self._restart()
            return None
        if self.history_button.handle_event(event):
            self._invalidate_search()
            return "history"
        if self.settings_button.handle_event(event):
            self._invalidate_search()
            return "settings"
        if self.analysis_button.handle_event(event):
            self.analysis_enabled = not self.analysis_enabled
            return None

        self.prev_button.enabled = self.review_index > 0
        self.next_button.enabled = self.review_index < len(self.state.history)
        if self.prev_button.handle_event(event):
            self.review_index -= 1
            return None
        if self.next_button.handle_event(event):
            self.review_index += 1
            return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_board_click(event.pos)
        return None

    def update(self) -> None:
        self.prev_button.enabled = self.review_index > 0
        self.next_button.enabled = self.review_index < len(self.state.history)
        self._collect_ai_result()

        if self.state.game_over:
            self._record_result_if_needed()
            return
        if self.review_index != len(self.state.history):
            return

        ai = self.ai_players.get(self.state.current_player)
        if ai is None:
            return
        if self.ai_search_thread is not None:
            if self.ai_search_thread.is_alive():
                return
            self.ai_search_thread = None
        now = pygame.time.get_ticks()
        if now - self.last_action_time < self.settings.ai_delay_ms:
            return

        player = self.state.current_player
        generation = self.search_generation
        board = self.state.board.copy()
        self.ai_error = ""
        self.ai_search_thread = Thread(
            target=self._run_ai_search,
            args=(
                generation,
                player,
                ai,
                board,
                self.settings.win_length,
                self._depth_for_ai(ai),
            ),
            daemon=True,
            name=f"caro-ai-{player}",
        )
        self.ai_search_thread.start()

    def _run_ai_search(
        self,
        generation: int,
        player: int,
        ai: GameAI,
        board: Board,
        win_length: int,
        depth: int,
    ) -> None:
        """Chạy tìm kiếm trên bản sao bàn cờ, không gọi API Pygame."""
        try:
            move, metrics = ai.choose_move(
                board,
                player,
                win_length,
                depth,
            )
            self.ai_results.put((generation, player, move, metrics, ""))
        except Exception as exc:  # Bảo vệ game loop trước lỗi worker.
            self.ai_results.put((generation, player, None, SearchMetrics(), str(exc)))

    def _collect_ai_result(self) -> None:
        try:
            result = self.ai_results.get_nowait()
        except Empty:
            return

        generation, player, move, metrics, error = result
        self.ai_search_thread = None
        if generation != self.search_generation:
            return
        if self.state.game_over or player != self.state.current_player:
            return

        self.ai_error = error
        self.last_metrics = metrics
        self.last_ai_player = player
        if move is not None and self.state.play_move(*move):
            move_number = len(self.state.history)
            ai = self.ai_players[player]
            depth = metrics.depth or self._depth_for_ai(ai)
            snapshot = SearchMetrics(
                execution_time_ms=metrics.execution_time_ms,
                nodes_expanded=metrics.nodes_expanded,
                score=metrics.score,
                depth=depth,
                pruned_branches=metrics.pruned_branches,
                analysis=metrics.analysis,
            )
            self.move_metrics[move_number] = MoveMetricRecord(
                move_number=move_number,
                player=player,
                actor_name=ai.name,
                algorithm_key=ai.key,
                depth=depth,
                metrics=snapshot,
            )
            self.game_total_time_ms += snapshot.execution_time_ms
            self.game_total_nodes += snapshot.nodes_expanded
            self.game_total_pruned += snapshot.pruned_branches
            self.game_ai_moves += 1
            self.review_index = len(self.state.history)
        self.last_action_time = pygame.time.get_ticks()
        self._record_result_if_needed()

    def _agent_name_for_player(self, player: int) -> str:
        ai = self.ai_players.get(player)
        return ai.name if ai is not None else "Human"

    def _record_result_if_needed(self) -> None:
        if not self.state.game_over or self.result_recorded:
            return
        for player in self.ai_players:
            stats = self.session_stats[player]
            stats["games"] += 1
            if self.state.winner == player:
                stats["wins"] += 1
            elif self.state.is_draw:
                stats["draws"] += 1
            else:
                stats["losses"] += 1
        if self.state.is_draw:
            result = "Hòa"
        else:
            result = f"{player_label(self.state.winner)} thắng"
        self.current_summary = MatchHistoryRecord(
            number=next_match_number(self.match_history),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mode_label=MATCH_MODE_LABELS[self.settings.match_mode],
            board_label=(
                f"{self.settings.rows}x{self.settings.cols}, "
                f"k={self.settings.win_length}"
            ),
            x_agent=self._agent_name_for_player(PLAYER_X),
            o_agent=self._agent_name_for_player(PLAYER_O),
            result=result,
            move_count=len(self.state.history),
            game_seed=self.game_seed,
            total_time_ms=self.game_total_time_ms,
            total_nodes=self.game_total_nodes,
            total_pruned=self.game_total_pruned,
            ai_move_count=self.game_ai_moves,
            rows=self.settings.rows,
            cols=self.settings.cols,
            win_length=self.settings.win_length,
            match_mode=self.settings.match_mode,
            ai_x_key=self.settings.ai_x,
            ai_o_key=self.settings.ai_o,
            winner=self.state.winner,
            is_draw=self.state.is_draw,
            moves=tuple(self.state.history),
            move_metrics=tuple(
                self.move_metrics[number] for number in sorted(self.move_metrics)
            ),
        )
        self.match_history.append(self.current_summary)
        self.history_error = ""
        if self.history_store is not None:
            try:
                self.history_store.save(self.match_history)
            except OSError as exc:
                self.history_error = str(exc)
        self.result_notice_started_at = pygame.time.get_ticks()
        self.result_recorded = True

    def _draw_history(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface,
            COLORS["panel"],
            self.HISTORY_PANEL,
            border_radius=16,
        )
        draw_text(
            surface,
            "MOVE HISTORY",
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
            history_text or "Chưa có nước đi",
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
        mode_text = "LIVE" if self.review_index == len(self.state.history) else "REVIEW"
        mode_color = COLORS["success"] if mode_text == "LIVE" else COLORS["accent"]
        draw_text(
            surface,
            mode_text,
            12,
            mode_color,
            (1234, 753),
            bold=True,
            anchor="midright",
        )

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(surface, COLORS["background"], COLORS["background_2"])
        self.menu_button.draw(surface)
        draw_panel(
            surface,
            self.student_panel,
            COLORS["panel"],
            radius=10,
            border_color=(57, 78, 110),
            shadow=False,
        )
        draw_text(
            surface,
            "24110158 - Nguyễn Gia Bảo, 24110157 - Nguyễn Thế Ân",
            13,
            COLORS["text"],
            self.student_panel.center,
            bold=True,
            anchor="center",
        )
        self.history_button.draw(surface)
        self.restart_button.draw(surface)
        self.settings_button.draw(surface)
        draw_text(
            surface,
            "CARO",
            26,
            COLORS["text"],
            (162, 21),
            bold=True,
        )
        draw_text(
            surface,
            f"{self.settings.rows} x {self.settings.cols}  •  k={self.settings.win_length}",
            13,
            COLORS["muted"],
            (164, 51),
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
            self.result_notice_started_at,
            self.RESULT_NOTICE_MS,
            show_analysis=self.analysis_enabled,
            analysis=(
                analysis_record.analysis if analysis_record is not None else None
            ),
        )
        self.metrics_panel.draw(
            surface,
            MetricsPanelContext(
                settings=self.settings,
                state=self.state,
                review_index=self.review_index,
                ai_players=self.ai_players,
                move_metrics=self.move_metrics,
                last_ai_player=self.last_ai_player,
                session_stats=self.session_stats,
                current_summary=self.current_summary,
                is_ai_thinking=self.is_ai_thinking,
                ai_error=self.ai_error,
                history_error=self.history_error,
                game_seed=self.game_seed,
            ),
        )
        self._draw_history(surface)
