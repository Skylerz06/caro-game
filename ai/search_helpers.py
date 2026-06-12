"""Helper dùng chung cho pipeline tìm kiếm AI."""

from __future__ import annotations

from dataclasses import dataclass, field

from game.board import Board
from game.rules import check_win
from utils.helpers import (
    WIN_SCORE,
    SearchAnalysis,
    SearchMetrics,
    build_search_analysis,
    evaluate_board,
)


@dataclass
class RootSearchTracker:
    """Theo dõi kết quả ứng viên và quyết định tại tầng gốc."""

    algorithm_key: str
    score_label: str
    best_move: tuple[int, int] | None = None
    best_score: float = float("-inf")
    results: list[tuple[int, int, float, bool, int]] = field(default_factory=list)

    def record(
        self,
        row: int,
        col: int,
        score: float,
        terminal_win: bool,
        pruned_branches: int = 0,
    ) -> None:
        self.results.append((row, col, score, terminal_win, pruned_branches))
        if score > self.best_score:
            self.best_score = score
            self.best_move = (row, col)

    def apply_to(self, metrics: SearchMetrics) -> SearchAnalysis:
        metrics.score = self.best_score if self.best_move is not None else 0.0
        metrics.analysis = build_search_analysis(
            self.algorithm_key,
            self.score_label,
            self.results,
            self.best_move,
        )
        return metrics.analysis


def terminal_or_leaf_score(
    board: Board,
    depth: int,
    maximizing_player: int,
    win_length: int,
    last_move: tuple[int, int],
    last_player: int,
) -> float | None:
    """Trả điểm nếu node đã kết thúc/đạt depth, ngược lại trả None."""
    row, col = last_move
    if check_win(board, row, col, last_player, win_length):
        if last_player == maximizing_player:
            return float(WIN_SCORE + depth)
        return float(-WIN_SCORE - depth)
    if board.is_full():
        return 0.0
    if depth <= 0:
        return evaluate_board(board, maximizing_player, win_length)
    return None
