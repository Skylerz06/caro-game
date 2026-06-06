"""Chạy các trận AI vs AI và tổng hợp số liệu trên terminal."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path

# Cho phép chạy trực tiếp: python experiments/evaluate.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai import create_ai
from config.settings import ALGORITHM_LABELS, ALGORITHMS
from game.board import PLAYER_O, PLAYER_X
from game.state import GameState


@dataclass
class AlgorithmStats:
    seats: int = 0
    wins: int = 0
    moves: int = 0
    time_ms: float = 0.0
    nodes: int = 0


@dataclass
class MatchupResult:
    ai_x: str
    ai_o: str
    x_wins: int = 0
    o_wins: int = 0
    draws: int = 0
    moves: int = 0
    time_ms: float = 0.0
    nodes: int = 0


def play_game(
    ai_x_key: str,
    ai_o_key: str,
    rows: int,
    cols: int,
    win_length: int,
    depth: int,
    global_stats: dict[str, AlgorithmStats],
) -> tuple[int, int, float, int]:
    """Trả về winner, số nước, tổng thời gian và tổng node."""
    state = GameState(rows, cols, win_length)
    agents = {
        PLAYER_X: (ai_x_key, create_ai(ai_x_key)),
        PLAYER_O: (ai_o_key, create_ai(ai_o_key)),
    }
    total_time = 0.0
    total_nodes = 0

    while not state.game_over:
        player = state.current_player
        key, agent = agents[player]
        move, metrics = agent.choose_move(
            state.board, player, win_length, depth
        )
        if move is None:
            break
        state.play_move(*move)
        total_time += metrics.execution_time_ms
        total_nodes += metrics.nodes_expanded
        stats = global_stats[key]
        stats.moves += 1
        stats.time_ms += metrics.execution_time_ms
        stats.nodes += metrics.nodes_expanded

    global_stats[ai_x_key].seats += 1
    global_stats[ai_o_key].seats += 1
    if state.winner == PLAYER_X:
        global_stats[ai_x_key].wins += 1
    elif state.winner == PLAYER_O:
        global_stats[ai_o_key].wins += 1

    return state.winner, len(state.history), total_time, total_nodes


def run_evaluation(args: argparse.Namespace) -> None:
    algorithms = args.algorithms
    global_stats = {key: AlgorithmStats() for key in algorithms}
    results: list[MatchupResult] = []

    for ai_x_key, ai_o_key in product(algorithms, repeat=2):
        result = MatchupResult(ai_x=ai_x_key, ai_o=ai_o_key)
        for _ in range(args.games):
            winner, moves, time_ms, nodes = play_game(
                ai_x_key,
                ai_o_key,
                args.rows,
                args.cols,
                args.win,
                args.depth,
                global_stats,
            )
            result.moves += moves
            result.time_ms += time_ms
            result.nodes += nodes
            if winner == PLAYER_X:
                result.x_wins += 1
            elif winner == PLAYER_O:
                result.o_wins += 1
            else:
                result.draws += 1
        results.append(result)

    print(
        f"\nĐÁNH GIÁ CARO {args.rows}x{args.cols}, "
        f"k={args.win}, depth={args.depth}, {args.games} trận/cặp\n"
    )
    header = (
        f"{'AI X':<16} {'AI O':<16} {'X thắng':>7} {'O thắng':>7} "
        f"{'Hòa':>5} {'ms/nước':>10} {'node/nước':>12}"
    )
    print(header)
    print("-" * len(header))
    for result in results:
        move_count = max(1, result.moves)
        print(
            f"{ALGORITHM_LABELS[result.ai_x]:<16} "
            f"{ALGORITHM_LABELS[result.ai_o]:<16} "
            f"{result.x_wins:>7} {result.o_wins:>7} "
            f"{result.draws:>5} "
            f"{result.time_ms / move_count:>10.2f} "
            f"{result.nodes / move_count:>12.1f}"
        )

    print("\nTỔNG HỢP THEO THUẬT TOÁN")
    summary_header = (
        f"{'Thuật toán':<16} {'Win rate':>10} "
        f"{'ms/nước':>12} {'node/nước':>12} {'Số nước':>10}"
    )
    print(summary_header)
    print("-" * len(summary_header))
    for key in algorithms:
        stats = global_stats[key]
        win_rate = stats.wins / stats.seats * 100 if stats.seats else 0.0
        move_count = max(1, stats.moves)
        print(
            f"{ALGORITHM_LABELS[key]:<16} {win_rate:>9.1f}% "
            f"{stats.time_ms / move_count:>12.2f} "
            f"{stats.nodes / move_count:>12.1f} "
            f"{stats.moves:>10}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Đánh giá Greedy, Minimax và Alpha-Beta bằng AI vs AI."
    )
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--cols", type=int, default=10)
    parser.add_argument("--win", type=int, default=5)
    parser.add_argument("--depth", type=int, choices=range(1, 5), default=2)
    parser.add_argument(
        "--games",
        type=int,
        default=1,
        help="Số trận cho mỗi cặp AI X/AI O.",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=ALGORITHMS,
        default=list(ALGORITHMS),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not (5 <= args.rows <= 20 and 5 <= args.cols <= 24):
        raise SystemExit("rows phải trong 5-20 và cols trong 5-24.")
    if not (3 <= args.win <= min(8, args.rows, args.cols)):
        raise SystemExit("win phải trong 3-8 và không vượt kích thước bàn.")
    if args.games < 1:
        raise SystemExit("games phải lớn hơn hoặc bằng 1.")
    run_evaluation(args)


if __name__ == "__main__":
    main()

