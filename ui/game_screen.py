"""Màn hình thi đấu, metrics và xem lại lịch sử."""

from __future__ import annotations

from datetime import datetime
from queue import Empty, Queue
from threading import Thread

import pygame

from ai import create_ai
from ai.base import GameAI
from config.settings import (
    ALGORITHM_LABELS,
    COLORS,
    MATCH_MODE_LABELS,
    GameSettings,
)
from game.board import Board, EMPTY, PLAYER_O, PLAYER_X
from game.match_history import MatchHistoryRecord, MoveMetricRecord
from game.state import GameState
from ui.components import (
    Button,
    IconButton,
    draw_gradient,
    draw_metric_card,
    draw_panel,
    draw_text,
)
from utils.helpers import SearchMetrics, player_label
from utils.seedmaker import derive_seed, new_global_seed


class GameScreen:
    BOARD_PANEL = pygame.Rect(24, 90, 840, 620)
    BOARD_AREA = pygame.Rect(42, 108, 804, 584)
    SIDE_PANEL = pygame.Rect(884, 90, 372, 620)
    HISTORY_PANEL = pygame.Rect(24, 724, 1232, 58)
    RESULT_NOTICE_MS = 5000

    def __init__(self, settings: GameSettings) -> None:
        self.settings = settings
        self.state = GameState(
            settings.rows, settings.cols, settings.win_length
        )
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
        self.match_history: list[MatchHistoryRecord] = []
        self.game_total_time_ms = 0.0
        self.game_total_nodes = 0
        self.game_total_pruned = 0
        self.game_ai_moves = 0
        self.result_notice_started_at = 0
        self.session_stats = {
            PLAYER_X: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
            PLAYER_O: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
        }

        self.menu_button = Button(pygame.Rect(24, 18, 116, 44), "MENU")
        self.restart_button = Button(
            pygame.Rect(1038, 18, 142, 44), "CHƠI LẠI"
        )
        self.history_button = Button(
            pygame.Rect(902, 18, 124, 44), "LỊCH SỬ"
        )
        self.settings_button = IconButton(
            pygame.Rect(1192, 16, 48, 48), "gear", tooltip="Cài đặt"
        )
        self.prev_button = IconButton(
            pygame.Rect(558, 732, 42, 42), "left"
        )
        self.next_button = IconButton(
            pygame.Rect(680, 732, 42, 42), "right"
        )
        self.start(settings)

    def start(
        self, settings: GameSettings, reset_session: bool = True
    ) -> None:
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
        if (
            self.ai_search_thread is not None
            and not self.ai_search_thread.is_alive()
        ):
            self.ai_search_thread = None

    @property
    def is_ai_thinking(self) -> bool:
        return bool(
            self.ai_search_thread is not None
            and self.ai_search_thread.is_alive()
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

    def _board_geometry(self) -> tuple[float, float, float]:
        cell_size = min(
            self.BOARD_AREA.width / self.settings.cols,
            self.BOARD_AREA.height / self.settings.rows,
        )
        width = cell_size * self.settings.cols
        height = cell_size * self.settings.rows
        origin_x = self.BOARD_AREA.centerx - width / 2
        origin_y = self.BOARD_AREA.centery - height / 2
        return origin_x, origin_y, cell_size

    def _handle_board_click(self, position: tuple[int, int]) -> None:
        if (
            self.state.game_over
            or not self._is_human_turn()
            or self.review_index != len(self.state.history)
        ):
            return

        origin_x, origin_y, cell_size = self._board_geometry()
        x, y = position
        col = int((x - origin_x) // cell_size)
        row = int((y - origin_y) // cell_size)
        board_width = cell_size * self.settings.cols
        board_height = cell_size * self.settings.rows
        inside = (
            origin_x <= x < origin_x + board_width
            and origin_y <= y < origin_y + board_height
        )
        player = self.state.current_player
        if inside and self.state.play_move(row, col):
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
            self.ai_results.put(
                (generation, player, move, metrics, "")
            )
        except Exception as exc:  # Bảo vệ game loop trước lỗi worker.
            self.ai_results.put(
                (generation, player, None, SearchMetrics(), str(exc))
            )

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
            number=len(self.match_history) + 1,
            timestamp=datetime.now().strftime("%H:%M:%S"),
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
        )
        self.match_history.append(self.current_summary)
        self.result_notice_started_at = pygame.time.get_ticks()
        self.result_recorded = True

    def _draw_piece(
        self,
        surface: pygame.Surface,
        player: int,
        center: tuple[int, int],
        cell_size: float,
    ) -> None:
        radius = max(6, int(cell_size * 0.30))
        width = max(2, int(cell_size * 0.09))
        if player == PLAYER_X:
            offset = int(radius * 0.75)
            pygame.draw.line(
                surface,
                COLORS["x"],
                (center[0] - offset, center[1] - offset),
                (center[0] + offset, center[1] + offset),
                width,
            )
            pygame.draw.line(
                surface,
                COLORS["x"],
                (center[0] + offset, center[1] - offset),
                (center[0] - offset, center[1] + offset),
                width,
            )
        elif player == PLAYER_O:
            pygame.draw.circle(
                surface, COLORS["o"], center, radius, width
            )

    def _draw_board(self, surface: pygame.Surface) -> None:
        draw_panel(
            surface,
            self.BOARD_PANEL,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )
        board = (
            self.state.board
            if self.review_index == len(self.state.history)
            else self.state.board_at(self.review_index)
        )
        origin_x, origin_y, cell_size = self._board_geometry()
        board_rect = pygame.Rect(
            round(origin_x),
            round(origin_y),
            round(cell_size * self.settings.cols),
            round(cell_size * self.settings.rows),
        )
        pygame.draw.rect(
            surface, COLORS["board"], board_rect, border_radius=10
        )

        winning = (
            set(self.state.winning_line)
            if self.review_index == len(self.state.history)
            else set()
        )
        last_move = (
            self.state.history[self.review_index - 1]
            if self.review_index > 0
            else None
        )

        for row in range(self.settings.rows):
            for col in range(self.settings.cols):
                left = origin_x + col * cell_size
                top = origin_y + row * cell_size
                cell_rect = pygame.Rect(
                    round(left),
                    round(top),
                    max(1, round(cell_size)),
                    max(1, round(cell_size)),
                )
                if (row, col) in winning:
                    pygame.draw.rect(
                        surface, (187, 247, 208), cell_rect
                    )
                pygame.draw.rect(
                    surface,
                    COLORS["board_line"],
                    cell_rect,
                    width=1,
                )

                player = board[row][col]
                if player != EMPTY:
                    center = (
                        round(left + cell_size / 2),
                        round(top + cell_size / 2),
                    )
                    self._draw_piece(surface, player, center, cell_size)
                    if (
                        last_move
                        and last_move.row == row
                        and last_move.col == col
                    ):
                        pygame.draw.circle(
                            surface,
                            COLORS["accent"],
                            center,
                            max(2, int(cell_size * 0.07)),
                        )

        notice_age = pygame.time.get_ticks() - self.result_notice_started_at
        show_result_notice = (
            self.state.game_over
            and self.review_index == len(self.state.history)
            and (
                self.result_notice_started_at == 0
                or notice_age <= self.RESULT_NOTICE_MS
            )
        )
        if show_result_notice:
            overlay = pygame.Surface((430, 100), pygame.SRCALPHA)
            pygame.draw.rect(
                overlay, (15, 23, 42, 225), overlay.get_rect(), border_radius=18
            )
            if self.state.is_draw:
                title = "VÁN ĐẤU HÒA"
                color = COLORS["accent"]
            else:
                title = f"NGƯỜI CHƠI {player_label(self.state.winner)} THẮNG"
                color = COLORS["success"]
            draw_text(
                overlay,
                title,
                24,
                color,
                (215, 24),
                bold=True,
                anchor="midtop",
            )
            draw_text(
                overlay,
                "Chọn CHƠI LẠI để bắt đầu ván mới",
                14,
                COLORS["text"],
                (215, 62),
                anchor="midtop",
            )
            surface.blit(
                overlay,
                (
                    self.BOARD_PANEL.centerx - 215,
                    self.BOARD_PANEL.centery - 50,
                ),
            )

    def _metric_record_for_panel(self) -> MoveMetricRecord | None:
        if self.review_index != len(self.state.history):
            return self.move_metrics.get(self.review_index)
        for move_number in range(len(self.state.history), 0, -1):
            record = self.move_metrics.get(move_number)
            if record is not None and record.algorithm_key is not None:
                return record
        return None

    def _metric_player(
        self, record: MoveMetricRecord | None = None
    ) -> int | None:
        if record is not None:
            return record.player
        if self.state.current_player in self.ai_players:
            return self.state.current_player
        if self.last_ai_player is not None:
            return self.last_ai_player
        if self.ai_players:
            return next(iter(self.ai_players))
        return None

    def _draw_side_panel(self, surface: pygame.Surface) -> None:
        draw_panel(
            surface,
            self.SIDE_PANEL,
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

        if self.review_index != len(self.state.history):
            status = "ĐANG XEM LẠI"
            status_color = COLORS["accent"]
        elif self.is_ai_thinking:
            status = "AI ĐANG TÍNH..."
            status_color = COLORS["accent"]
        elif self.state.game_over:
            status = "KẾT THÚC"
            status_color = COLORS["success"]
        else:
            status = f"LƯỢT {player_label(self.state.current_player)}"
            status_color = (
                COLORS["x"]
                if self.state.current_player == PLAYER_X
                else COLORS["o"]
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

        record = self._metric_record_for_panel()
        live_ai_turn = (
            self.review_index == len(self.state.history)
            and not self.state.game_over
            and self.state.current_player in self.ai_players
        )
        metric_player = (
            self.state.current_player
            if live_ai_turn
            else self._metric_player(record)
        )
        current_agent = self.ai_players.get(metric_player)
        metric = (
            record.metrics
            if record is not None and record.algorithm_key is not None
            else None
        )

        if live_ai_turn and current_agent is not None:
            current_ai = current_agent.name
            if current_agent.key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            else:
                depth_note = f"Depth: {self._depth_for_ai(current_agent)}"
            move_note = "Current turn"
            if record is not None:
                move_note = (
                    f"Metric: Move {record.move_number} "
                    f"{player_label(record.player)}"
                )
        elif record is not None:
            current_ai = record.actor_name
            if record.algorithm_key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            elif record.algorithm_key is not None:
                depth_note = f"Depth: {record.depth}"
            else:
                depth_note = "Move by human"
            move_note = (
                f"Move {record.move_number}: "
                f"{player_label(record.player)}"
            )
        else:
            current_ai = current_agent.name if current_agent else "Human"
            if current_agent is None:
                depth_note = ""
            elif current_agent.key == "greedy":
                depth_note = "Depth: 1 (fixed)"
            else:
                depth_note = f"Depth: {self._depth_for_ai(current_agent)}"
            move_note = "Current turn"

        if current_agent is None and record is None:
            depth_note = ""

        stats = (
            self.session_stats[metric_player]
            if metric_player in self.ai_players
            else {"wins": 0, "draws": 0, "losses": 0, "games": 0}
        )
        win_rate = (
            f"{stats['wins'] / stats['games'] * 100:.1f}%"
            if stats["games"]
            else "N/A"
        )
        if self.state.game_over and self.current_summary is not None:
            if self.current_summary.ai_move_count:
                total_value = (
                    f"{self.current_summary.average_time_ms:.2f} ms/move"
                )
                total_note = self.current_summary.total_line
            else:
                total_value = f"{self.current_summary.move_count} moves"
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
                        if live_ai_turn and self.is_ai_thinking
                        else "N/A"
                    )
                ),
                COLORS["accent"],
                "",
            ),
            (
                "Nodes Expanded",
                (
                    f"{metric.nodes_expanded:,}"
                    if metric is not None
                    else (
                        "Đang tính..."
                        if live_ai_turn and self.is_ai_thinking
                        else "N/A"
                    )
                ),
                COLORS["text"],
                (
                    f"Pruned: {metric.pruned_branches:,}"
                    if metric is not None and metric.pruned_branches
                    else ""
                ),
            ),
            (
                "Current AI",
                current_ai,
                COLORS["primary"],
                depth_note,
            ),
            (
                "Move Count",
                (
                    f"{self.review_index} / {len(self.state.history)}"
                    if self.review_index != len(self.state.history)
                    else str(len(self.state.history))
                ),
                COLORS["text"],
                move_note,
            ),
            (
                "Win Rate",
                win_rate,
                COLORS["success"],
                (
                    (
                        f"W-D-L: {stats['wins']}-"
                        f"{stats['draws']}-{stats['losses']}"
                    )
                    if stats["games"]
                    else "Session"
                ),
            ),
            (
                "Game Total",
                total_value,
                COLORS["success"] if self.state.game_over else COLORS["muted"],
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
            f"Chế độ: {MATCH_MODE_LABELS[self.settings.match_mode]}",
            12,
            COLORS["muted"],
            (904, 638),
        )
        draw_text(
            surface,
            f"Điều kiện thắng: {self.settings.win_length} quân liên tiếp",
            12,
            COLORS["muted"],
            (904, 658),
        )
        if self.settings.match_mode == "ai_ai":
            matchup = (
                f"X: {ALGORITHM_LABELS[self.settings.ai_x]}  |  "
                f"O: {ALGORITHM_LABELS[self.settings.ai_o]}"
            )
            draw_text(
                surface,
                matchup,
                11,
                COLORS["muted"],
                (904, 678),
            )
        if self.ai_error:
            draw_text(
                surface,
                f"AI error: {self.ai_error[:36]}",
                11,
                COLORS["danger"],
                (904, 698),
            )
        else:
            draw_text(
                surface,
                f"Game seed: {self.game_seed:016X}",
                11,
                COLORS["muted"],
                (904, 698),
            )

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
        draw_text(
            surface,
            f"{self.review_index} / {len(self.state.history)}",
            15,
            COLORS["text"],
            (640, 753),
            bold=True,
            anchor="center",
        )
        mode_text = (
            "LIVE"
            if self.review_index == len(self.state.history)
            else "REVIEW"
        )
        mode_color = (
            COLORS["success"] if mode_text == "LIVE" else COLORS["accent"]
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

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(
            surface, COLORS["background"], COLORS["background_2"]
        )
        self.menu_button.draw(surface)
        self.history_button.draw(surface)
        self.restart_button.draw(surface)
        self.settings_button.draw(surface)
        draw_text(
            surface,
            "CARO AI LAB",
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
        self._draw_board(surface)
        self._draw_side_panel(surface)
        self._draw_history(surface)
