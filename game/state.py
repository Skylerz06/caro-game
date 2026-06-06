"""Trạng thái ván đấu và lịch sử nước đi."""

from __future__ import annotations

from dataclasses import dataclass

from game.board import Board, EMPTY, PLAYER_O, PLAYER_X
from game.rules import check_win, get_winning_line


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    player: int
    number: int

    @property
    def notation(self) -> str:
        """Ký hiệu dạng A1, B3... phù hợp phần lịch sử."""
        return f"{column_name(self.col)}{self.row + 1}"


def column_name(col: int) -> str:
    """Đổi chỉ số cột thành A..Z, AA.. để hỗ trợ bàn rộng."""
    name = ""
    value = col + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        name = chr(65 + remainder) + name
    return name


class GameState:
    """Điều phối lượt chơi, kết quả và khả năng xem lại."""

    def __init__(self, rows: int, cols: int, win_length: int) -> None:
        self.rows = rows
        self.cols = cols
        self.win_length = win_length
        self.board = Board(rows, cols)
        self.current_player = PLAYER_X
        self.winner = EMPTY
        self.is_draw = False
        self.game_over = False
        self.history: list[Move] = []
        self.winning_line: list[tuple[int, int]] = []

    @property
    def last_move(self) -> Move | None:
        return self.history[-1] if self.history else None

    def reset(self) -> None:
        self.board.reset()
        self.current_player = PLAYER_X
        self.winner = EMPTY
        self.is_draw = False
        self.game_over = False
        self.history.clear()
        self.winning_line.clear()

    def play_move(self, row: int, col: int) -> bool:
        """Đánh một nước hợp lệ và cập nhật trạng thái kết thúc."""
        if self.game_over:
            return False

        player = self.current_player
        if not self.board.place(row, col, player):
            return False

        move = Move(row, col, player, len(self.history) + 1)
        self.history.append(move)

        if check_win(
            self.board, row, col, player, self.win_length
        ):
            self.winner = player
            self.game_over = True
            self.winning_line = get_winning_line(
                self.board, row, col, player, self.win_length
            )
        elif self.board.is_full():
            self.is_draw = True
            self.game_over = True
        else:
            self.current_player = PLAYER_O if player == PLAYER_X else PLAYER_X
        return True

    def board_at(self, move_index: int) -> Board:
        """Dựng lại bàn cờ sau move_index nước để xem lịch sử."""
        index = max(0, min(move_index, len(self.history)))
        board = Board(self.rows, self.cols)
        board.load_moves(
            (move.row, move.col, move.player)
            for move in self.history[:index]
        )
        return board

