"""Chạy các trận AI vs AI và tổng hợp số liệu trên terminal."""

from __future__ import annotations

import argparse
import random
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
from utils.seedmaker import derive_seed, new_global_seed


@dataclass
class AlgorithmStats:
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
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
    depths: dict[str, int],
    global_stats: dict[str, AlgorithmStats],
    opening: list[tuple[int, int]],
    count_for_summary: bool,
    game_seed: int,
) -> tuple[int, int, float, int]:
    """Trả về winner, số nước, tổng thời gian và tổng node."""
    state = GameState(rows, cols, win_length)
    agents = {
        PLAYER_X: (
            ai_x_key,
            create_ai(
                ai_x_key,
                seed=derive_seed(game_seed, "ai:x"),
                randomize_ties=True,
            ),
        ),
        PLAYER_O: (
            ai_o_key,
            create_ai(
                ai_o_key,
                seed=derive_seed(game_seed, "ai:o"),
                randomize_ties=True,
            ),
        ),
    }
    total_time = 0.0
    total_nodes = 0
    searched_moves = 0

    for row, col in opening:
        if state.game_over or not state.play_move(row, col):
            break

    while not state.game_over:
        player = state.current_player
        key, agent = agents[player]
        move, metrics = agent.choose_move(
            state.board, player, win_length, depths.get(key, 1)
        )
        if move is None:
            break
        state.play_move(*move)
        total_time += metrics.execution_time_ms
        total_nodes += metrics.nodes_expanded
        searched_moves += 1
        if count_for_summary:
            stats = global_stats[key]
            stats.moves += 1
            stats.time_ms += metrics.execution_time_ms
            stats.nodes += metrics.nodes_expanded

    if count_for_summary:
        for player, (key, _) in agents.items():
            stats = global_stats[key]
            stats.games += 1
            if state.winner == player:
                stats.wins += 1
            elif state.is_draw:
                stats.draws += 1
            else:
                stats.losses += 1

    return state.winner, searched_moves, total_time, total_nodes


def generate_opening(
    rows: int,
    cols: int,
    win_length: int,
    move_count: int,
    seed: int,
) -> list[tuple[int, int]]:
    """Tạo thế khai cuộc tái lập để nhiều trận không hoàn toàn giống nhau."""
    rng = random.Random(seed)
    state = GameState(rows, cols, win_length)
    opening: list[tuple[int, int]] = []
    for _ in range(move_count):
        candidates = state.board.candidate_moves(radius=2)
        if not candidates:
            break
        move = rng.choice(candidates)
        if not state.play_move(*move):
            break
        opening.append(move)
        if state.game_over:
            break
    return opening


def run_evaluation(args: argparse.Namespace) -> None:
    algorithms = args.algorithms
    global_stats = {key: AlgorithmStats() for key in algorithms}
    results: list[MatchupResult] = []
    depths = {
        "greedy": 1,
        "minimax": args.minimax_depth,
        "alphabeta": args.alphabeta_depth,
    }
    global_seed = new_global_seed()
    game_seeds = [
        derive_seed(global_seed, f"game:{game_index}")
        for game_index in range(args.games)
    ]
    openings = [
        generate_opening(
            args.rows,
            args.cols,
            args.win,
            args.opening_moves,
            derive_seed(game_seeds[game_index], "opening"),
        )
        for game_index in range(args.games)
    ]

    for ai_x_key, ai_o_key in product(algorithms, repeat=2):
        result = MatchupResult(ai_x=ai_x_key, ai_o=ai_o_key)
        for game_index in range(args.games):
            winner, moves, time_ms, nodes = play_game(
                ai_x_key,
                ai_o_key,
                args.rows,
                args.cols,
                args.win,
                depths,
                global_stats,
                openings[game_index],
                ai_x_key != ai_o_key,
                game_seeds[game_index],
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
        f"k={args.win}, {args.games} trận/cặp\n"
        f"Depth: Greedy=1, Minimax={args.minimax_depth}, "
        f"Alpha-Beta={args.alphabeta_depth}\n"
        f"Global seed phiên chạy: {global_seed}\n"
    )
    for game_index, (game_seed, opening) in enumerate(
        zip(game_seeds, openings), 1
    ):
        print(
            f"  Case {game_index}: game_seed={game_seed}, "
            f"opening={opening}"
        )
    print()
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

    total_games = sum(
        result.x_wins + result.o_wins + result.draws
        for result in results
    )
    total_x_wins = sum(result.x_wins for result in results)
    total_o_wins = sum(result.o_wins for result in results)
    total_draws = sum(result.draws for result in results)
    print(
        "\nẢNH HƯỞNG THỨ TỰ ĐI: "
        f"X thắng {total_x_wins}/{total_games}, "
        f"O thắng {total_o_wins}/{total_games}, hòa {total_draws}. "
        "Win rate tổng hợp bên dưới đã cân bằng hai vị trí X/O."
    )

    print("\nTỔNG HỢP ĐỐI ĐẦU KHÁC THUẬT TOÁN")
    summary_header = (
        f"{'Thuật toán':<16} {'W-D-L':>11} {'Win rate':>10} "
        f"{'Score rate':>11} {'ms/nước':>11} {'node/nước':>11}"
    )
    print(summary_header)
    print("-" * len(summary_header))
    for key in algorithms:
        stats = global_stats[key]
        win_rate = stats.wins / stats.games * 100 if stats.games else 0.0
        score_rate = (
            (stats.wins + 0.5 * stats.draws) / stats.games * 100
            if stats.games
            else 0.0
        )
        move_count = max(1, stats.moves)
        print(
            f"{ALGORITHM_LABELS[key]:<16} "
            f"{stats.wins:>3}-{stats.draws}-{stats.losses:<3} "
            f"{win_rate:>9.1f}% {score_rate:>10.1f}% "
            f"{stats.time_ms / move_count:>11.2f} "
            f"{stats.nodes / move_count:>11.1f}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Đánh giá Greedy, Minimax và Alpha-Beta bằng AI vs AI."
    )
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--cols", type=int, default=10)
    parser.add_argument("--win", type=int, default=5)
    parser.add_argument(
        "--depth",
        type=int,
        choices=range(1, 5),
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--minimax-depth", type=int, choices=range(1, 5), default=2
    )
    parser.add_argument(
        "--alphabeta-depth", type=int, choices=range(1, 5), default=2
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1,
        help="Số trận cho mỗi cặp AI X/AI O.",
    )
    parser.add_argument(
        "--opening-moves",
        type=int,
        default=2,
        help="Số nước khai cuộc ngẫu nhiên trước khi AI tìm kiếm.",
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
    if args.depth is not None:
        args.minimax_depth = args.depth
        args.alphabeta_depth = args.depth
    if not (3 <= args.rows <= 20 and 3 <= args.cols <= 24):
        raise SystemExit("rows phải trong 3-20 và cols trong 3-24.")
    if not (3 <= args.win <= min(8, args.rows, args.cols)):
        raise SystemExit("win phải trong 3-8 và không vượt kích thước bàn.")
    if args.games < 1:
        raise SystemExit("games phải lớn hơn hoặc bằng 1.")
    if not 0 <= args.opening_moves <= 6:
        raise SystemExit("opening-moves phải trong 0-6.")
    run_evaluation(args)


if __name__ == "__main__":
    main()
