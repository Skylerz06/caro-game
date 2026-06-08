"""Lớp cha chung cho các thuật toán AI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from random import Random

from game.board import Board
from utils.helpers import SearchMetrics


class GameAI(ABC):
    """Lớp cha giúp các AI dùng chung cấu hình tie-breaking."""

    name = "Base AI"
    key = "base"

    def __init__(
        self,
        seed: int | None = None,
        randomize_ties: bool = True,
    ) -> None:
        self.tie_rng = Random(seed) if randomize_ties else None

    @abstractmethod
    def choose_move(
        self,
        board: Board,
        player: int,
        win_length: int,
        depth: int = 2,
    ) -> tuple[tuple[int, int] | None, SearchMetrics]:
        """Chọn nước đi và trả về số liệu tìm kiếm."""
        raise NotImplementedError
