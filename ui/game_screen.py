"""Màn hình thi đấu, metrics và xem lại lịch sử."""

from __future__ import annotations

from dataclasses import replace
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
from game.metrics import SearchTotals, new_session_stats
from game.state import GameState
from ui.board_view import BoardView
from ui.components import (
    Button,
    IconButton,
    draw_gradient,
    draw_panel,
    draw_text,
    is_left_click,
)
from ui.metrics_panel import MetricsPanel, MetricsPanelContext
from ui.move_history_bar import MoveHistoryBar
from utils.helpers import SearchMetrics, player_label
from utils.seedmaker import derive_seed, new_global_seed


class GameScreen:
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
        self.history_bar = MoveHistoryBar(analysis_enabled=False)
        self.state = GameState(
            settings.rows,
            settings.cols,
            settings.win_length,
            self._starting_player(settings),
        )
        self.ai_players: dict[int, GameAI] = {}
        self.last_ai_player: int | None = None
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
        self.search_totals = SearchTotals()
        self.result_notice_started_at = 0
        self.session_stats = new_session_stats()

        self.menu_button = Button(pygame.Rect(24, 18, 116, 44), "MENU")
        self.student_panel = pygame.Rect(310, 18, 570, 44)
        self.restart_button = Button(pygame.Rect(1038, 18, 142, 44), "CHƠI LẠI")
        self.history_button = Button(pygame.Rect(902, 18, 124, 44), "LỊCH SỬ")
        self.settings_button = IconButton(
            pygame.Rect(1192, 16, 48, 48), "gear", tooltip="Cài đặt"
        )
        self.start(settings)

    def _reset_match(self, *, recreate_state: bool, reset_session: bool) -> None:
        if recreate_state:
            self.state = GameState(
                self.settings.rows,
                self.settings.cols,
                self.settings.win_length,
                self._starting_player(self.settings),
            )
        else:
            self.state.reset()
        self._create_ai_players()
        self.last_ai_player = None
        self.history_bar.reset(0)
        self.last_action_time = pygame.time.get_ticks()
        self.result_recorded = False
        self.ai_error = ""
        self.history_error = ""
        self.move_metrics = {}
        self.current_summary = None
        self.search_totals = SearchTotals()
        self.result_notice_started_at = 0
        if reset_session:
            self.session_stats = new_session_stats()

    def start(self, settings: GameSettings, reset_session: bool = True) -> None:
        self._invalidate_search()
        self.settings = GameSettings.from_dict(settings.to_dict())
        self._reset_match(recreate_state=True, reset_session=reset_session)

    def _restart(self) -> None:
        self._invalidate_search()
        self._reset_match(recreate_state=False, reset_session=False)

    @staticmethod
    def _starting_player(settings: GameSettings) -> int:
        if settings.match_mode == "human_ai" and settings.human_ai_first == "ai":
            return PLAYER_O
        return PLAYER_X

    def _create_ai_players(self) -> None:
        """Create configured agents from one new seed per match."""
        self.game_seed = new_global_seed()
        keys = {}
        if self.settings.match_mode == "human_ai":
            keys = {PLAYER_O: self.settings.ai_o}
        elif self.settings.match_mode == "ai_ai":
            keys = {PLAYER_X: self.settings.ai_x, PLAYER_O: self.settings.ai_o}
        self.ai_players = {
            player: create_ai(
                key,
                seed=derive_seed(self.game_seed, f"ai:{player_label(player).lower()}"),
            )
            for player, key in keys.items()
        }

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

    def _handle_board_click(self, position: tuple[int, int]) -> None:
        if (
            self.state.game_over
            or not self._is_human_turn()
            or self.history_bar.review_index != len(self.state.history)
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
            self.history_bar.review_index = len(self.state.history)
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
        if self.history_bar.handle_event(event, len(self.state.history)):
            return None

        if is_left_click(event):
            self._handle_board_click(event.pos)
        return None

    def update(self) -> None:
        self.history_bar.sync(len(self.state.history))
        self._collect_ai_result()

        if self.state.game_over:
            self._record_result_if_needed()
            return
        if self.history_bar.review_index != len(self.state.history):
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
                self.settings.depth_for_algorithm(ai.key),
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
        self.last_ai_player = player
        if move is not None and self.state.play_move(*move):
            move_number = len(self.state.history)
            ai = self.ai_players[player]
            depth = metrics.depth or self.settings.depth_for_algorithm(ai.key)
            snapshot = replace(metrics, depth=depth)
            self.move_metrics[move_number] = MoveMetricRecord(
                move_number=move_number,
                player=player,
                actor_name=ai.name,
                algorithm_key=ai.key,
                depth=depth,
                metrics=snapshot,
            )
            self.search_totals.add(snapshot)
            self.history_bar.move_to_latest(len(self.state.history))
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
            outcome = (
                "draws"
                if self.state.is_draw
                else "wins"
                if self.state.winner == player
                else "losses"
            )
            stats["games"] += 1
            stats[outcome] += 1
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
            total_time_ms=self.search_totals.execution_time_ms,
            total_nodes=self.search_totals.nodes_expanded,
            total_pruned=self.search_totals.pruned_branches,
            ai_move_count=self.search_totals.move_count,
            rows=self.settings.rows,
            cols=self.settings.cols,
            win_length=self.settings.win_length,
            match_mode=self.settings.match_mode,
            human_ai_first=self.settings.human_ai_first,
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
            self.history_bar.review_index,
            len(self.state.history),
        )
        self.board_view.draw(
            surface,
            self.state,
            self.settings,
            self.history_bar.review_index,
            self.result_notice_started_at,
            self.RESULT_NOTICE_MS,
            show_analysis=self.history_bar.analysis_enabled,
            analysis=(
                analysis_record.analysis if analysis_record is not None else None
            ),
        )
        self.metrics_panel.draw(
            surface,
            MetricsPanelContext(
                settings=self.settings,
                state=self.state,
                review_index=self.history_bar.review_index,
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
        live = self.history_bar.review_index == len(self.state.history)
        self.history_bar.draw(
            surface,
            self.state.history,
            title="MOVE HISTORY",
            empty_text="Chưa có nước đi",
            mode_text="LIVE" if live else "REVIEW",
            mode_color=COLORS["success"] if live else COLORS["accent"],
        )
