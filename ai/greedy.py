"""Greedy Search: chọn nước có lượng giá tốt nhất sau một lượt."""

from __future__ import annotations

from time import perf_counter

from ai.base import GameAI
from game.board import Board
from game.rules import check_win
from utils.helpers import (
    WIN_SCORE,
    SearchMetrics,
    build_search_analysis,
    evaluate_board,
    ordered_moves,
)


class GreedyAI(GameAI):
    name = "Greedy Search"
    key = "greedy"

    def choose_move(
        self,
        board: Board,
        player: int,
        win_length: int,
        depth: int = 1,
    ) -> tuple[tuple[int, int] | None, SearchMetrics]:
        start = perf_counter()
        metrics = SearchMetrics(depth=1)
        working = board.copy()
        moves = ordered_moves(
            working,
            player,
            win_length,
            tie_rng=self.tie_rng,
        )

        best_move: tuple[int, int] | None = None
        best_score = float("-inf")
        candidate_results: list[tuple[int, int, float, bool, int]] = []

        for row, col in moves:
            metrics.nodes_expanded += 1
            working.place(row, col, player)
            terminal_win = check_win(working, row, col, player, win_length)
            if terminal_win:
                score = float(WIN_SCORE)
            else:
                score = evaluate_board(working, player, win_length)
            working.remove(row, col)
            candidate_results.append((row, col, score, terminal_win, 0))

            if score > best_score:
                best_score = score
                best_move = (row, col)

        metrics.score = best_score if best_move is not None else 0.0
        metrics.analysis = build_search_analysis(
            self.key,
            "Heuristic",
            candidate_results,
            best_move,
        )
        metrics.execution_time_ms = (perf_counter() - start) * 1000
        return best_move, metrics
