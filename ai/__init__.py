"""Nhà máy tạo các thuật toán AI."""

from __future__ import annotations

from ai.alphabeta import AlphaBetaAI
from ai.greedy import GreedyAI
from ai.minimax import MinimaxAI


def create_ai(
    algorithm: str,
    *,
    seed: int | None = None,
    randomize_ties: bool = True,
):
    if algorithm == "greedy":
        return GreedyAI(seed=seed, randomize_ties=randomize_ties)
    if algorithm == "minimax":
        return MinimaxAI(seed=seed, randomize_ties=randomize_ties)
    if algorithm == "alphabeta":
        return AlphaBetaAI(seed=seed, randomize_ties=randomize_ties)
    raise ValueError(f"Thuật toán AI không hợp lệ: {algorithm}")


__all__ = ["AlphaBetaAI", "GreedyAI", "MinimaxAI", "create_ai"]
