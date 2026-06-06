"""Giao diện chung cho các thuật toán AI."""

from __future__ import annotations

from typing import Protocol

from game.board import Board
from utils.helpers import SearchMetrics


class GameAI(Protocol):
    name: str
    key: str

    def choose_move(
        self,
        board: Board,
        player: int,
        win_length: int,
        depth: int = 2,
    ) -> tuple[tuple[int, int] | None, SearchMetrics]:
        """Chọn nước đi và trả về số liệu tìm kiếm."""
        ...

