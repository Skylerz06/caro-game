"""Chạy các trận AI vs AI và tổng hợp số liệu trên terminal."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

# Cho phép chạy trực tiếp: python experiments/evaluate.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai import create_ai
from config.settings import ALGORITHM_LABELS, ALGORITHMS
from game.board import PLAYER_O, PLAYER_X
from game.metrics import SearchTotals
from game.state import GameState
from utils.seedmaker import derive_seed, new_global_seed


@dataclass
class AlgorithmStats:
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    search: SearchTotals = field(default_factory=SearchTotals)


@dataclass
class MatchupResult:
    ai_x: str
    ai_o: str
    x_wins: int = 0
    o_wins: int = 0
    draws: int = 0
    search: SearchTotals = field(default_factory=SearchTotals)


@dataclass(frozen=True)
class GameCase:
    index: int
    game_seed: int
    opening: list[tuple[int, int]]


@dataclass
class EvaluationResult:
    rows: int
    cols: int
    win_length: int
    games_per_matchup: int
    opening_moves: int
    algorithms: list[str]
    depths: dict[str, int]
    global_seed: int
    cases: list[GameCase]
    matchups: list[MatchupResult]
    algorithm_stats: dict[str, AlgorithmStats]


def _search_totals_dict(totals: SearchTotals) -> dict[str, int | float]:
    return {
        "execution_time_ms": totals.execution_time_ms,
        "nodes_expanded": totals.nodes_expanded,
        "pruned_branches": totals.pruned_branches,
        "move_count": totals.move_count,
    }


def evaluation_to_dict(result: EvaluationResult) -> dict[str, Any]:
    """Chuyển kết quả sang cấu trúc JSON ổn định cho báo cáo."""
    return {
        "schema_version": 1,
        "configuration": {
            "rows": result.rows,
            "cols": result.cols,
            "win_length": result.win_length,
            "games_per_matchup": result.games_per_matchup,
            "opening_moves": result.opening_moves,
            "algorithms": result.algorithms,
            "depths": result.depths,
            "global_seed": result.global_seed,
        },
        "cases": [
            {
                "index": case.index,
                "game_seed": case.game_seed,
                "opening": [list(move) for move in case.opening],
            }
            for case in result.cases
        ],
        "matchups": [
            {
                "ai_x": matchup.ai_x,
                "ai_o": matchup.ai_o,
                "x_wins": matchup.x_wins,
                "o_wins": matchup.o_wins,
                "draws": matchup.draws,
                "search": _search_totals_dict(matchup.search),
            }
            for matchup in result.matchups
        ],
        "algorithm_stats": {
            key: {
                "games": stats.games,
                "wins": stats.wins,
                "draws": stats.draws,
                "losses": stats.losses,
                "search": _search_totals_dict(stats.search),
            }
            for key, stats in result.algorithm_stats.items()
        },
    }


def save_evaluation_json(result: EvaluationResult, output_path: Path) -> None:
    """Lưu dữ liệu thô để tổng hợp bảng và kiểm tra lại seed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(evaluation_to_dict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
) -> tuple[int, int, float, int, int]:
    """Trả về winner, số nước, thời gian, node và số nhánh cắt."""
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
    totals = SearchTotals()

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
        totals.add(metrics)
        if count_for_summary:
            global_stats[key].search.add(metrics)

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

    return (
        state.winner,
        totals.move_count,
        totals.execution_time_ms,
        totals.nodes_expanded,
        totals.pruned_branches,
    )


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


def run_evaluation(args: argparse.Namespace) -> EvaluationResult:
    algorithms = args.algorithms
    matchups = product(algorithms, repeat=2)
    global_stats = {key: AlgorithmStats() for key in algorithms}
    results: list[MatchupResult] = []
    depths = {
        "greedy": 1,
        "minimax": args.minimax_depth,
        "alphabeta": args.alphabeta_depth,
    }
    global_seed = args.global_seed if args.global_seed is not None else new_global_seed()
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

    for ai_x_key, ai_o_key in matchups:
        result = MatchupResult(ai_x=ai_x_key, ai_o=ai_o_key)
        for game_index in range(args.games):
            winner, moves, time_ms, nodes, pruned = play_game(
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
            result.search.move_count += moves
            result.search.execution_time_ms += time_ms
            result.search.nodes_expanded += nodes
            result.search.pruned_branches += pruned
            if winner == PLAYER_X:
                result.x_wins += 1
            elif winner == PLAYER_O:
                result.o_wins += 1
            else:
                result.draws += 1
        results.append(result)

    return EvaluationResult(
        rows=args.rows,
        cols=args.cols,
        win_length=args.win,
        games_per_matchup=args.games,
        opening_moves=args.opening_moves,
        algorithms=list(algorithms),
        depths=depths,
        global_seed=global_seed,
        cases=[
            GameCase(index=index, game_seed=game_seed, opening=opening)
            for index, (game_seed, opening) in enumerate(
                zip(game_seeds, openings), 1
            )
        ],
        matchups=results,
        algorithm_stats=global_stats,
    )


def print_evaluation(result: EvaluationResult) -> None:
    """In bảng kết quả tương thích với giao diện dòng lệnh trước đây."""
    print(
        f"\nĐÁNH GIÁ CARO {result.rows}x{result.cols}, "
        f"k={result.win_length}, {result.games_per_matchup} trận/cặp\n"
        f"Depth: Greedy=1, Minimax={result.depths['minimax']}, "
        f"Alpha-Beta={result.depths['alphabeta']}\n"
        f"Global seed phiên chạy: {result.global_seed}\n"
    )
    for case in result.cases:
        print(
            f"  Case {case.index}: game_seed={case.game_seed}, "
            f"opening={case.opening}"
        )
    print()
    header = (
        f"{'AI X':<16} {'AI O':<16} {'X thắng':>7} {'O thắng':>7} "
        f"{'Hòa':>5} {'ms/nước':>10} {'node/nước':>12}"
    )
    print(header)
    print("-" * len(header))
    for matchup in result.matchups:
        move_count = max(1, matchup.search.move_count)
        print(
            f"{ALGORITHM_LABELS[matchup.ai_x]:<16} "
            f"{ALGORITHM_LABELS[matchup.ai_o]:<16} "
            f"{matchup.x_wins:>7} {matchup.o_wins:>7} "
            f"{matchup.draws:>5} "
            f"{matchup.search.execution_time_ms / move_count:>10.2f} "
            f"{matchup.search.nodes_expanded / move_count:>12.1f}"
        )

    total_games = sum(
        matchup.x_wins + matchup.o_wins + matchup.draws
        for matchup in result.matchups
    )
    total_x_wins = sum(matchup.x_wins for matchup in result.matchups)
    total_o_wins = sum(matchup.o_wins for matchup in result.matchups)
    total_draws = sum(matchup.draws for matchup in result.matchups)
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
    for key in result.algorithms:
        stats = result.algorithm_stats[key]
        win_rate = stats.wins / stats.games * 100 if stats.games else 0.0
        score_rate = (
            (stats.wins + 0.5 * stats.draws) / stats.games * 100 if stats.games else 0.0
        )
        move_count = max(1, stats.search.move_count)
        print(
            f"{ALGORITHM_LABELS[key]:<16} "
            f"{stats.wins:>3}-{stats.draws}-{stats.losses:<3} "
            f"{win_rate:>9.1f}% {score_rate:>10.1f}% "
            f"{stats.search.execution_time_ms / move_count:>11.2f} "
            f"{stats.search.nodes_expanded / move_count:>11.1f}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Đánh giá Greedy, Minimax và Alpha-Beta bằng AI vs AI."
    )
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--cols", type=int, default=10)
    parser.add_argument("--win", type=int, default=5)
    parser.add_argument("--minimax-depth", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--alphabeta-depth", type=int, choices=range(1, 5), default=2)
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
    parser.add_argument(
        "--global-seed",
        type=int,
        default=None,
        help="Seed phiên chạy để tái lập khai cuộc và quyết định AI.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Đường dẫn lưu dữ liệu thô JSON schema v1.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not (3 <= args.rows <= 20 and 3 <= args.cols <= 24):
        raise SystemExit("rows phải trong 3-20 và cols trong 3-24.")
    if not (3 <= args.win <= min(8, args.rows, args.cols)):
        raise SystemExit("win phải trong 3-8 và không vượt kích thước bàn.")
    if args.games < 1:
        raise SystemExit("games phải lớn hơn hoặc bằng 1.")
    if not 0 <= args.opening_moves <= 6:
        raise SystemExit("opening-moves phải trong 0-6.")
    result = run_evaluation(args)
    print_evaluation(result)
    if args.json_output is not None:
        save_evaluation_json(result, args.json_output)
        print(f"\nĐã lưu dữ liệu JSON: {args.json_output}")


if __name__ == "__main__":
    main()
