"""Cấu trúc tổng hợp metrics tìm kiếm qua nhiều nước đi."""

from __future__ import annotations

from dataclasses import dataclass

from game.board import PLAYER_O, PLAYER_X
from utils.helpers import SearchMetrics


@dataclass
class SearchTotals:
    """Cộng dồn metrics mà không làm thay đổi snapshot từng nước."""

    execution_time_ms: float = 0.0
    nodes_expanded: int = 0
    pruned_branches: int = 0
    move_count: int = 0

    def add(self, metrics: SearchMetrics) -> None:
        self.execution_time_ms += metrics.execution_time_ms
        self.nodes_expanded += metrics.nodes_expanded
        self.pruned_branches += metrics.pruned_branches
        self.move_count += 1


def new_session_stats() -> dict[int, dict[str, int]]:
    """Tạo bảng W-D-L rỗng cho cả hai người chơi."""
    return {
        PLAYER_X: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
        PLAYER_O: {"wins": 0, "draws": 0, "losses": 0, "games": 0},
    }
