"""Bản ghi metric từng nước và dữ liệu replay của trận đấu."""

from __future__ import annotations

from dataclasses import dataclass

from game.state import GameState, Move
from utils.helpers import SearchAnalysis, SearchMetrics


@dataclass(frozen=True)
class MoveMetricRecord:
    """Metric gắn với một nước đi cụ thể để xem lại trong move history."""

    move_number: int
    player: int
    actor_name: str
    algorithm_key: str | None
    depth: int
    metrics: SearchMetrics

    @property
    def analysis(self) -> SearchAnalysis | None:
        return self.metrics.analysis


def metric_record_for_view(
    move_metrics: dict[int, MoveMetricRecord],
    review_index: int,
    history_length: int,
) -> MoveMetricRecord | None:
    """Lấy đúng metric của nước review hoặc AI gần nhất ở chế độ live."""
    if review_index != history_length:
        return move_metrics.get(review_index)
    for move_number in range(history_length, 0, -1):
        record = move_metrics.get(move_number)
        if record is not None and record.algorithm_key is not None:
            return record
    return None


@dataclass(frozen=True)
class MatchHistoryRecord:
    """Tổng kết và dữ liệu đầy đủ của một ván đã kết thúc."""

    number: int
    timestamp: str
    mode_label: str
    board_label: str
    x_agent: str
    o_agent: str
    result: str
    move_count: int
    game_seed: int
    total_time_ms: float
    total_nodes: int
    total_pruned: int
    ai_move_count: int
    rows: int = 0
    cols: int = 0
    win_length: int = 0
    match_mode: str = "human_human"
    ai_x_key: str = "minimax"
    ai_o_key: str = "alphabeta"
    winner: int = 0
    is_draw: bool = False
    moves: tuple[Move, ...] = ()
    move_metrics: tuple[MoveMetricRecord, ...] = ()

    @property
    def average_time_ms(self) -> float:
        if self.ai_move_count <= 0:
            return 0.0
        return self.total_time_ms / self.ai_move_count

    @property
    def average_nodes(self) -> float:
        if self.ai_move_count <= 0:
            return 0.0
        return self.total_nodes / self.ai_move_count

    @property
    def total_line(self) -> str:
        """Chuỗi tổng kết ngắn dạng A | B | C cho UI."""
        return (
            f"{self.total_time_ms:.1f} ms | "
            f"{self.total_nodes:,} nodes | "
            f"{self.ai_move_count} AI moves"
        )

    @property
    def average_line(self) -> str:
        """Chuỗi trung bình theo nước AI để tránh nhầm với tổng."""
        return (
            f"{self.average_time_ms:.2f} ms/move | "
            f"{self.average_nodes:.1f} nodes/move | "
            f"{self.total_pruned:,} pruned"
        )

    @property
    def metrics_by_move(self) -> dict[int, MoveMetricRecord]:
        return {record.move_number: record for record in self.move_metrics}

    def build_state(self) -> GameState:
        """Dựng lại trạng thái cuối trận và xác thực chuỗi nước đi."""
        if self.rows <= 0 or self.cols <= 0 or self.win_length <= 0:
            raise ValueError("Kích thước replay không hợp lệ.")
        state = GameState(self.rows, self.cols, self.win_length)
        for expected_number, move in enumerate(self.moves, start=1):
            if move.number != expected_number:
                raise ValueError("Số thứ tự nước đi không liên tục.")
            if state.current_player != move.player:
                raise ValueError("Thứ tự người chơi trong replay không hợp lệ.")
            if not state.play_move(move.row, move.col):
                raise ValueError("Replay chứa nước đi không hợp lệ.")
        return state


def next_match_number(records: list[MatchHistoryRecord]) -> int:
    """Sinh số trận tiếp theo, kể cả khi file có khoảng trống."""
    return max((record.number for record in records), default=0) + 1
