"""Minimax có cắt tỉa Alpha-Beta."""

from __future__ import annotations

from time import perf_counter

from ai.base import GameAI
from ai.search_helpers import RootSearchTracker, terminal_or_leaf_score
from game.board import Board
from game.rules import check_win
from utils.helpers import (
    WIN_SCORE,
    SearchMetrics,
    branch_limit_for_depth,
    evaluate_board,
    opponent,
    ordered_moves,
)


class AlphaBetaAI(GameAI):
    name = "Alpha-Beta"
    key = "alphabeta"

    def choose_move(
        self,
        board: Board,
        player: int,
        win_length: int,
        depth: int = 2,
    ) -> tuple[tuple[int, int] | None, SearchMetrics]:
        start = perf_counter()
        depth = max(1, depth)
        metrics = SearchMetrics(depth=depth)
        working = board.copy()
        limit = branch_limit_for_depth(depth)
        moves = ordered_moves(
            working,
            player,
            win_length,
            limit,
            tie_rng=self.tie_rng,
        )

        alpha = float("-inf")
        beta = float("inf")
        tracker = RootSearchTracker(self.key, "Alpha-Beta Value")

        for row, col in moves:
            working.place(row, col, player)
            metrics.nodes_expanded += 1
            terminal_win = check_win(working, row, col, player, win_length)
            pruned_before = metrics.pruned_branches
            if terminal_win:
                score = float(WIN_SCORE + depth)
            else:
                score = self._alphabeta(
                    working,
                    depth - 1,
                    opponent(player),
                    player,
                    win_length,
                    (row, col),
                    player,
                    alpha,
                    beta,
                    metrics,
                    limit,
                )
            working.remove(row, col)
            tracker.record(
                row,
                col,
                score,
                terminal_win,
                metrics.pruned_branches - pruned_before,
            )
            alpha = max(alpha, tracker.best_score)

        tracker.apply_to(metrics)
        metrics.execution_time_ms = (perf_counter() - start) * 1000
        return tracker.best_move, metrics

    def _alphabeta(
        self,
        board: Board,
        depth: int,
        current_player: int,
        maximizing_player: int,
        win_length: int,
        last_move: tuple[int, int],
        last_player: int,
        alpha: float,
        beta: float,
        metrics: SearchMetrics,
        branch_limit: int,
    ) -> float:
        terminal_score = terminal_or_leaf_score(
            board,
            depth,
            maximizing_player,
            win_length,
            last_move,
            last_player,
        )
        if terminal_score is not None:
            return terminal_score

        moves = ordered_moves(board, current_player, win_length, branch_limit)
        if not moves:
            return evaluate_board(board, maximizing_player, win_length)

        if current_player == maximizing_player:
            value = float("-inf")
            for next_row, next_col in moves:
                board.place(next_row, next_col, current_player)
                metrics.nodes_expanded += 1
                value = max(
                    value,
                    self._alphabeta(
                        board,
                        depth - 1,
                        opponent(current_player),
                        maximizing_player,
                        win_length,
                        (next_row, next_col),
                        current_player,
                        alpha,
                        beta,
                        metrics,
                        branch_limit,
                    ),
                )
                board.remove(next_row, next_col)
                alpha = max(alpha, value)
                if alpha >= beta:
                    metrics.pruned_branches += 1
                    break
            return value

        value = float("inf")
        for next_row, next_col in moves:
            board.place(next_row, next_col, current_player)
            metrics.nodes_expanded += 1
            value = min(
                value,
                self._alphabeta(
                    board,
                    depth - 1,
                    opponent(current_player),
                    maximizing_player,
                    win_length,
                    (next_row, next_col),
                    current_player,
                    alpha,
                    beta,
                    metrics,
                    branch_limit,
                ),
            )
            board.remove(next_row, next_col)
            beta = min(beta, value)
            if alpha >= beta:
                metrics.pruned_branches += 1
                break
        return value
