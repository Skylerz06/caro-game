"""Heuristic và cấu trúc dữ liệu dùng chung cho các AI."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from random import Random

from game.board import Board, EMPTY, PLAYER_O, PLAYER_X
from game.rules import DIRECTIONS, check_win


WIN_SCORE = 1_000_000_000
BRANCH_LIMITS = {1: 24, 2: 16, 3: 10, 4: 7}


@dataclass(frozen=True)
class CandidateScore:
    """Điểm quyết định của một nước ứng viên tại tầng gốc."""

    row: int
    col: int
    score: float
    rank: int
    selected: bool = False
    terminal_win: bool = False
    pruned_branches: int = 0


@dataclass(frozen=True)
class SearchAnalysis:
    """Snapshot gọn để giải thích cách AI chọn nước đi."""

    algorithm_key: str
    score_label: str
    candidates: tuple[CandidateScore, ...]

    @property
    def selected(self) -> CandidateScore | None:
        return next(
            (candidate for candidate in self.candidates if candidate.selected),
            None,
        )


@dataclass
class SearchMetrics:
    """Thông tin phục vụ panel đo lường và thí nghiệm."""

    execution_time_ms: float = 0.0
    nodes_expanded: int = 0
    score: float = 0.0
    depth: int = 0
    pruned_branches: int = 0
    analysis: SearchAnalysis | None = None


def build_search_analysis(
    algorithm_key: str,
    score_label: str,
    results: list[tuple[int, int, float, bool, int]],
    selected_move: tuple[int, int] | None,
) -> SearchAnalysis:
    """Xếp hạng kết quả tầng gốc mà không lượng giá lại bàn cờ."""
    ranked_indices = sorted(
        range(len(results)),
        key=lambda index: (-results[index][2], index),
    )
    ranks = {
        result_index: rank for rank, result_index in enumerate(ranked_indices, start=1)
    }
    candidates = tuple(
        CandidateScore(
            row=row,
            col=col,
            score=score,
            rank=ranks[index],
            selected=(row, col) == selected_move,
            terminal_win=terminal_win,
            pruned_branches=pruned_branches,
        )
        for index, (row, col, score, terminal_win, pruned_branches) in enumerate(
            results
        )
    )
    return SearchAnalysis(
        algorithm_key=algorithm_key,
        score_label=score_label,
        candidates=candidates,
    )


def format_search_score(score: float) -> str:
    """Rút gọn điểm lớn để hiển thị nhất quán trong UI."""
    absolute = abs(score)
    if absolute >= 1_000_000_000:
        return f"{score / 1_000_000_000:.2f}B"
    if absolute >= 1_000_000:
        return f"{score / 1_000_000:.2f}M"
    if absolute >= 1_000:
        return f"{score / 1_000:.2f}K"
    return f"{score:,.1f}"


def opponent(player: int) -> int:
    return PLAYER_O if player == PLAYER_X else PLAYER_X


def player_label(player: int) -> str:
    if player == PLAYER_X:
        return "X"
    if player == PLAYER_O:
        return "O"
    return "-"


def branch_limit_for_depth(depth: int) -> int:
    """Minimax và Alpha-Beta phải duyệt cùng một cây ở cùng độ sâu."""
    return BRANCH_LIMITS.get(max(1, depth), BRANCH_LIMITS[4])


def pattern_weight(
    count: int,
    open_ends: int,
    win_length: int,
) -> float:
    """Chấm điểm chuỗi theo độ dài và số đầu còn mở."""
    if count <= 0:
        return 0.0
    if count >= win_length:
        return float(WIN_SCORE)
    if open_ends <= 0:
        return 0.0

    distance = win_length - count
    if distance == 1:
        return 4_000_000.0 if open_ends == 2 else 350_000.0
    if distance == 2:
        return 80_000.0 if open_ends == 2 else 8_000.0

    base = float(10 ** min(count, 5))
    return base * (3.0 if open_ends == 2 else 1.0)


def _score_player_patterns(
    board: Board,
    player: int,
    win_length: int,
) -> float:
    """Duyệt các chuỗi liên tiếp tối đại theo bốn hướng."""
    score = 0.0
    for row in range(board.rows):
        for col in range(board.cols):
            if board[row][col] != player:
                continue
            for d_row, d_col in DIRECTIONS:
                previous_row = row - d_row
                previous_col = col - d_col
                if (
                    board.inside(previous_row, previous_col)
                    and board[previous_row][previous_col] == player
                ):
                    continue

                length = 0
                next_row, next_col = row, col
                while (
                    board.inside(next_row, next_col)
                    and board[next_row][next_col] == player
                ):
                    length += 1
                    next_row += d_row
                    next_col += d_col

                open_ends = 0
                if (
                    board.inside(previous_row, previous_col)
                    and board[previous_row][previous_col] == EMPTY
                ):
                    open_ends += 1
                if (
                    board.inside(next_row, next_col)
                    and board[next_row][next_col] == EMPTY
                ):
                    open_ends += 1
                score += pattern_weight(length, open_ends, win_length)
    return score


def evaluate_board(
    board: Board,
    maximizing_player: int,
    win_length: int,
) -> float:
    """Hàm lượng giá: chuỗi của ta cộng điểm, chuỗi địch trừ điểm."""
    enemy = opponent(maximizing_player)
    score = _score_player_patterns(board, maximizing_player, win_length)
    # Phòng thủ được ưu tiên nhẹ để AI ít bỏ sót đe dọa.
    score -= 1.12 * _score_player_patterns(board, enemy, win_length)

    center_row = (board.rows - 1) / 2
    center_col = (board.cols - 1) / 2
    for row in range(board.rows):
        for col in range(board.cols):
            value = board[row][col]
            if value == EMPTY:
                continue
            center_bonus = max(
                0.0,
                board.rows + board.cols - abs(row - center_row) - abs(col - center_col),
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
    tie_rng: Random | None = None,
) -> list[tuple[int, int]]:
    """Sắp nước tốt trước; có thể xáo trộn các nước đồng hạng."""
    enemy = opponent(player)
    center_row = (board.rows - 1) / 2
    center_col = (board.cols - 1) / 2
    ranked: list[tuple[float, tuple[int, int]]] = []
    winning_moves: list[tuple[float, tuple[int, int]]] = []
    blocking_moves: list[tuple[float, tuple[int, int]]] = []

    for row, col in board.candidate_moves(radius=2):
        attack_score = _neighbor_score(board, row, col, player)
        defense_score = _neighbor_score(board, row, col, enemy)
        # Xếp cả nước tấn công lẫn phòng thủ trước khi giới hạn nhánh.
        # Nếu chỉ xét quân của AI, các đầu chuỗi mở 3/4 của đối thủ có thể
        # bị loại khỏi cây tìm kiếm dù Minimax/Alpha-Beta đủ độ sâu.
        priority = attack_score + 1.25 * defense_score

        board.place(row, col, player)
        is_winning_move = check_win(board, row, col, player, win_length)
        if is_winning_move:
            priority += WIN_SCORE
        board.remove(row, col)

        board.place(row, col, enemy)
        is_blocking_move = check_win(board, row, col, enemy, win_length)
        if is_blocking_move:
            priority += WIN_SCORE / 2
        board.remove(row, col)

        distance = abs(row - center_row) + abs(col - center_col)
        priority -= distance
        item = (priority, (row, col))
        ranked.append(item)
        if is_winning_move:
            winning_moves.append(item)
        elif is_blocking_move:
            blocking_moves.append(item)

    # Nước thắng ngay luôn tốt hơn mọi heuristic. Nếu không có, chỉ xét
    # các ô chặn đối thủ thắng ở lượt kế tiếp.
    selected = winning_moves or blocking_moves or ranked
    selected.sort(key=lambda item: item[0], reverse=True)
    if tie_rng is not None:
        shuffled: list[tuple[float, tuple[int, int]]] = []
        for _, group in groupby(selected, key=lambda item: item[0]):
            tied_moves = list(group)
            tie_rng.shuffle(tied_moves)
            shuffled.extend(tied_moves)
        selected = shuffled
    moves = [move for _, move in selected]
    return moves if limit is None else moves[:limit]
