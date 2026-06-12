"""Bản ghi metric từng nước và tổng kết trận đấu."""

from __future__ import annotations

from dataclasses import dataclass

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
    """Tổng kết một ván đã kết thúc trong phiên chạy hiện tại."""

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
