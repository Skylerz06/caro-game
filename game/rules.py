"""Luật thắng cho biến thể Gomoku m,n,k."""

from __future__ import annotations

from game.board import Board


DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def collect_line(
    board: Board,
    row: int,
    col: int,
    player: int,
    d_row: int,
    d_col: int,
) -> list[tuple[int, int]]:
    """Thu thập chuỗi liên tiếp đi qua nước vừa đánh."""
    backward: list[tuple[int, int]] = []
    next_row, next_col = row - d_row, col - d_col
    while board.inside(next_row, next_col):
        if board[next_row][next_col] != player:
            break
        backward.append((next_row, next_col))
        next_row -= d_row
        next_col -= d_col

    forward: list[tuple[int, int]] = []
    next_row, next_col = row + d_row, col + d_col
    while board.inside(next_row, next_col):
        if board[next_row][next_col] != player:
            break
        forward.append((next_row, next_col))
        next_row += d_row
        next_col += d_col

    return list(reversed(backward)) + [(row, col)] + forward


def get_winning_line(
    board: Board,
    row: int,
    col: int,
    player: int,
    win_length: int,
) -> list[tuple[int, int]]:
    """Trả về chuỗi thắng đầu tiên, chấp nhận chuỗi dài hơn k."""
    if not board.inside(row, col) or board[row][col] != player:
        return []
    for d_row, d_col in DIRECTIONS:
        line = collect_line(board, row, col, player, d_row, d_col)
        if len(line) >= win_length:
            return line
    return []


def check_win(
    board: Board,
    row: int,
    col: int,
    player: int,
    win_length: int,
) -> bool:
    return bool(get_winning_line(board, row, col, player, win_length))

