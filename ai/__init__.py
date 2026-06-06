"""Nhà máy tạo các thuật toán AI."""

from __future__ import annotations

from ai.alphabeta import AlphaBetaAI
from ai.greedy import GreedyAI
from ai.minimax import MinimaxAI


def create_ai(algorithm: str):
    if algorithm == "greedy":
        return GreedyAI()
    if algorithm == "minimax":
        return MinimaxAI()
    if algorithm == "alphabeta":
        return AlphaBetaAI()
    raise ValueError(f"Thuật toán AI không hợp lệ: {algorithm}")


__all__ = ["AlphaBetaAI", "GreedyAI", "MinimaxAI", "create_ai"]

