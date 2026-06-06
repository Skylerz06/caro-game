"""Mô hình bàn cờ độc lập với giao diện."""

from __future__ import annotations

from collections.abc import Iterable


EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1


class Board:
    """Lưu bàn cờ m x n bằng ma trận số nguyên."""

    def __init__(
        self,
        rows: int,
        cols: int,
        grid: list[list[int]] | None = None,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.grid = (
            [row[:] for row in grid]
            if grid is not None
            else [[EMPTY for _ in range(cols)] for _ in range(rows)]
        )
        self.move_count = sum(
            cell != EMPTY for row in self.grid for cell in row
        )

    def reset(self) -> None:
        self.grid = [
            [EMPTY for _ in range(self.cols)] for _ in range(self.rows)
        ]
        self.move_count = 0

    def copy(self) -> "Board":
        return Board(self.rows, self.cols, self.grid)

    def inside(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_valid_move(self, row: int, col: int) -> bool:
        return self.inside(row, col) and self.grid[row][col] == EMPTY

    def place(self, row: int, col: int, player: int) -> bool:
        if not self.is_valid_move(row, col):
            return False
        self.grid[row][col] = player
        self.move_count += 1
        return True

    def remove(self, row: int, col: int) -> None:
        """Hoàn tác nước đi; chủ yếu dùng trong cây tìm kiếm AI."""
        if self.inside(row, col) and self.grid[row][col] != EMPTY:
            self.grid[row][col] = EMPTY
            self.move_count -= 1

    def is_full(self) -> bool:
        return self.move_count >= self.rows * self.cols

    def empty_cells(self) -> list[tuple[int, int]]:
        return [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == EMPTY
        ]

    def candidate_moves(self, radius: int = 2) -> list[tuple[int, int]]:
        """Chỉ lấy ô gần quân đã đánh để giảm không gian tìm kiếm."""
        if self.move_count == 0:
            return [(self.rows // 2, self.cols // 2)]

        candidates: set[tuple[int, int]] = set()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == EMPTY:
                    continue
                for d_row in range(-radius, radius + 1):
                    for d_col in range(-radius, radius + 1):
                        next_row = row + d_row
                        next_col = col + d_col
                        if self.is_valid_move(next_row, next_col):
                            candidates.add((next_row, next_col))

        center_row = (self.rows - 1) / 2
        center_col = (self.cols - 1) / 2
        return sorted(
            candidates,
            key=lambda move: (
                abs(move[0] - center_row) + abs(move[1] - center_col),
                move[0],
                move[1],
            ),
        )

    def load_moves(self, moves: Iterable[tuple[int, int, int]]) -> None:
        self.reset()
        for row, col, player in moves:
            self.place(row, col, player)

    def __getitem__(self, row: int) -> list[int]:
        return self.grid[row]

