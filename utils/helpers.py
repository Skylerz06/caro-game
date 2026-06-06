"""Heuristic và cấu trúc dữ liệu dùng chung cho các AI."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf

from game.board import Board, EMPTY, PLAYER_O, PLAYER_X
from game.rules import DIRECTIONS, check_win


WIN_SCORE = 1_000_000_000


@dataclass
class SearchMetrics:
    """Thông tin phục vụ panel đo lường và thí nghiệm."""

    execution_time_ms: float = 0.0
    nodes_expanded: int = 0
    score: float = 0.0
    depth: int = 0
    pruned_branches: int = 0


def opponent(player: int) -> int:
    return PLAYER_O if player == PLAYER_X else PLAYER_X


def player_label(player: int) -> str:
    if player == PLAYER_X:
        return "X"
    if player == PLAYER_O:
        return "O"
    return "-"


def pattern_weight(count: int, win_length: int) -> float:
    """Trọng số tăng theo cấp số nhân khi chuỗi gần đạt k."""
    if count <= 0:
        return 0.0
    if count >= win_length:
        return float(WIN_SCORE)
    return float(8 ** count)


def _iter_windows(board: Board, win_length: int):
    """Sinh mọi cửa sổ dài k theo bốn hướng."""
    for row in range(board.rows):
        for col in range(board.cols):
            for d_row, d_col in DIRECTIONS:
                end_row = row + (win_length - 1) * d_row
                end_col = col + (win_length - 1) * d_col
                if not board.inside(end_row, end_col):
                    continue
                yield [
                    board[row + step * d_row][col + step * d_col]
                    for step in range(win_length)
                ]


def evaluate_board(
    board: Board,
    maximizing_player: int,
    win_length: int,
) -> float:
    """Hàm lượng giá: chuỗi của ta cộng điểm, chuỗi địch trừ điểm."""
    enemy = opponent(maximizing_player)
    score = 0.0
    for window in _iter_windows(board, win_length):
        own_count = window.count(maximizing_player)
        enemy_count = window.count(enemy)
        if own_count and enemy_count:
            continue
        if own_count:
            score += pattern_weight(own_count, win_length)
        elif enemy_count:
            # Phòng thủ được ưu tiên nhẹ để AI ít bỏ sót đe dọa.
            score -= 1.12 * pattern_weight(enemy_count, win_length)

    center_row = (board.rows - 1) / 2
    center_col = (board.cols - 1) / 2
    for row in range(board.rows):
        for col in range(board.cols):
            value = board[row][col]
            if value == EMPTY:
                continue
            center_bonus = max(
                0.0,
                board.rows + board.cols
                - abs(row - center_row)
                - abs(col - center_col),
            )
            score += center_bonus if value == maximizing_player else -center_bonus
    return score


def _neighbor_score(board: Board, row: int, col: int, player: int) -> float:
    """Ước lượng nhanh sức mạnh cục bộ của một nước đi."""
    score = 0.0
    for d_row, d_col in DIRECTIONS:
        own = 1
        blocked = 0
        for sign in (-1, 1):
            for distance in range(1, 5):
                next_row = row + sign * distance * d_row
                next_col = col + sign * distance * d_col
                if not board.inside(next_row, next_col):
                    blocked += 1
                    break
                value = board[next_row][next_col]
                if value == player:
                    own += 1
                elif value == EMPTY:
                    break
                else:
                    blocked += 1
                    break
        score += (own * own * 12) - blocked * 2
    return score


def ordered_moves(
    board: Board,
    player: int,
    win_length: int,
    limit: int | None = None,
) -> list[tuple[int, int]]:
    """Sắp nước thắng/chặn thắng lên trước để tìm kiếm hiệu quả hơn."""
    enemy = opponent(player)
    center_row = (board.rows - 1) / 2
    center_col = (board.cols - 1) / 2
    ranked: list[tuple[float, tuple[int, int]]] = []

    for row, col in board.candidate_moves(radius=2):
        priority = _neighbor_score(board, row, col, player)

        board.place(row, col, player)
        if check_win(board, row, col, player, win_length):
            priority += WIN_SCORE
        board.remove(row, col)

        board.place(row, col, enemy)
        if check_win(board, row, col, enemy, win_length):
            priority += WIN_SCORE / 2
        board.remove(row, col)

        distance = abs(row - center_row) + abs(col - center_col)
        priority -= distance
        ranked.append((priority, (row, col)))

    ranked.sort(key=lambda item: item[0], reverse=True)
    moves = [move for _, move in ranked]
    return moves if limit is None else moves[:limit]


def terminal_score(
    winner: int,
    maximizing_player: int,
    depth_remaining: int,
) -> float:
    if winner == maximizing_player:
        return float(WIN_SCORE + depth_remaining)
    if winner == opponent(maximizing_player):
        return float(-WIN_SCORE - depth_remaining)
    return -inf

