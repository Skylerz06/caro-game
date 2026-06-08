"""Minimax có cắt tỉa Alpha-Beta."""

from __future__ import annotations

from time import perf_counter

from ai.base import GameAI
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
        best_move: tuple[int, int] | None = None
        best_score = float("-inf")

        for row, col in moves:
            working.place(row, col, player)
            metrics.nodes_expanded += 1
            if check_win(working, row, col, player, win_length):
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

            if score > best_score:
                best_score = score
                best_move = (row, col)
            alpha = max(alpha, best_score)

        metrics.score = best_score if best_move is not None else 0.0
        metrics.execution_time_ms = (perf_counter() - start) * 1000
        return best_move, metrics

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
        row, col = last_move
        if check_win(board, row, col, last_player, win_length):
            if last_player == maximizing_player:
                return float(WIN_SCORE + depth)
            return float(-WIN_SCORE - depth)
        if board.is_full():
            return 0.0
        if depth <= 0:
            return evaluate_board(board, maximizing_player, win_length)

        moves = ordered_moves(
            board, current_player, win_length, branch_limit
        )
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
