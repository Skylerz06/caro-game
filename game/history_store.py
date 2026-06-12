"""Lưu và tải lịch sử trận đấu bằng JSON có version."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from game.board import PLAYER_O, PLAYER_X
from game.match_history import MatchHistoryRecord, MoveMetricRecord
from game.state import Move
from utils.helpers import CandidateScore, SearchAnalysis, SearchMetrics


ROOT_DIR = Path(__file__).resolve().parents[1]
MATCH_HISTORY_FILE = ROOT_DIR / "utils" / "match_history.json"
SCHEMA_VERSION = 1


class MatchHistoryStore:
    """Persistence JSON độc lập với UI và game loop."""

    def __init__(self, path: Path = MATCH_HISTORY_FILE) -> None:
        self.path = path

    def load(self) -> list[MatchHistoryRecord]:
        """Đọc các record hợp lệ; file thiếu/hỏng trả về danh sách rỗng."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return []
        if not isinstance(payload, dict):
            return []
        if payload.get("schema_version") != SCHEMA_VERSION:
            return []
        raw_matches = payload.get("matches")
        if not isinstance(raw_matches, list):
            return []

        records: list[MatchHistoryRecord] = []
        for raw_record in raw_matches:
            try:
                records.append(_record_from_dict(raw_record))
            except (KeyError, TypeError, ValueError):
                continue
        records.sort(key=lambda record: record.number)
        return records

    def save(self, records: list[MatchHistoryRecord]) -> None:
        """Ghi nguyên tử để tránh làm hỏng file khi chương trình dừng giữa chừng."""
        payload = {
            "schema_version": SCHEMA_VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "matches": [_record_to_dict(record) for record in records],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        finally:
            if temporary.exists():
                temporary.unlink()


def _candidate_to_dict(candidate: CandidateScore) -> dict[str, Any]:
    return {
        "row": candidate.row,
        "col": candidate.col,
        "score": candidate.score,
        "rank": candidate.rank,
        "selected": candidate.selected,
        "terminal_win": candidate.terminal_win,
        "pruned_branches": candidate.pruned_branches,
    }


def _analysis_to_dict(analysis: SearchAnalysis | None) -> dict[str, Any] | None:
    if analysis is None:
        return None
    return {
        "algorithm_key": analysis.algorithm_key,
        "score_label": analysis.score_label,
        "candidates": [
            _candidate_to_dict(candidate) for candidate in analysis.candidates
        ],
    }


def _metrics_to_dict(metrics: SearchMetrics) -> dict[str, Any]:
    return {
        "execution_time_ms": metrics.execution_time_ms,
        "nodes_expanded": metrics.nodes_expanded,
        "score": metrics.score,
        "depth": metrics.depth,
        "pruned_branches": metrics.pruned_branches,
        "analysis": _analysis_to_dict(metrics.analysis),
    }


def _move_metric_to_dict(record: MoveMetricRecord) -> dict[str, Any]:
    return {
        "move_number": record.move_number,
        "player": record.player,
        "actor_name": record.actor_name,
        "algorithm_key": record.algorithm_key,
        "depth": record.depth,
        "metrics": _metrics_to_dict(record.metrics),
    }


def _record_to_dict(record: MatchHistoryRecord) -> dict[str, Any]:
    return {
        "number": record.number,
        "timestamp": record.timestamp,
        "config": {
            "rows": record.rows,
            "cols": record.cols,
            "win_length": record.win_length,
            "match_mode": record.match_mode,
            "ai_x": record.ai_x_key,
            "ai_o": record.ai_o_key,
        },
        "labels": {
            "mode": record.mode_label,
            "board": record.board_label,
            "x_agent": record.x_agent,
            "o_agent": record.o_agent,
            "result": record.result,
        },
        "result": {
            "winner": record.winner,
            "is_draw": record.is_draw,
        },
        "game_seed": record.game_seed,
        "totals": {
            "move_count": record.move_count,
            "total_time_ms": record.total_time_ms,
            "total_nodes": record.total_nodes,
            "total_pruned": record.total_pruned,
            "ai_move_count": record.ai_move_count,
        },
        "moves": [
            {
                "number": move.number,
                "row": move.row,
                "col": move.col,
                "player": move.player,
                "notation": move.notation,
            }
            for move in record.moves
        ],
        "move_metrics": [
            _move_metric_to_dict(metric) for metric in record.move_metrics
        ],
    }


def _candidate_from_dict(data: dict[str, Any]) -> CandidateScore:
    return CandidateScore(
        row=int(data["row"]),
        col=int(data["col"]),
        score=float(data["score"]),
        rank=int(data["rank"]),
        selected=bool(data.get("selected", False)),
        terminal_win=bool(data.get("terminal_win", False)),
        pruned_branches=int(data.get("pruned_branches", 0)),
    )


def _analysis_from_dict(data: Any) -> SearchAnalysis | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise TypeError("Analysis phải là object hoặc null.")
    raw_candidates = data.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise TypeError("Candidates phải là danh sách.")
    return SearchAnalysis(
        algorithm_key=str(data["algorithm_key"]),
        score_label=str(data["score_label"]),
        candidates=tuple(
            _candidate_from_dict(candidate) for candidate in raw_candidates
        ),
    )


def _metrics_from_dict(data: dict[str, Any]) -> SearchMetrics:
    return SearchMetrics(
        execution_time_ms=float(data.get("execution_time_ms", 0.0)),
        nodes_expanded=int(data.get("nodes_expanded", 0)),
        score=float(data.get("score", 0.0)),
        depth=int(data.get("depth", 0)),
        pruned_branches=int(data.get("pruned_branches", 0)),
        analysis=_analysis_from_dict(data.get("analysis")),
    )


def _move_metric_from_dict(data: dict[str, Any]) -> MoveMetricRecord:
    algorithm_key = data.get("algorithm_key")
    return MoveMetricRecord(
        move_number=int(data["move_number"]),
        player=int(data["player"]),
        actor_name=str(data["actor_name"]),
        algorithm_key=(str(algorithm_key) if algorithm_key is not None else None),
        depth=int(data.get("depth", 0)),
        metrics=_metrics_from_dict(data.get("metrics", {})),
    )


def _record_from_dict(data: Any) -> MatchHistoryRecord:
    if not isinstance(data, dict):
        raise TypeError("Match record phải là object.")
    config = data["config"]
    labels = data["labels"]
    result = data["result"]
    totals = data["totals"]
    raw_moves = data.get("moves", [])
    raw_metrics = data.get("move_metrics", [])
    if not all(isinstance(value, dict) for value in (config, labels, result, totals)):
        raise TypeError("Các nhóm dữ liệu trận phải là object.")
    if not isinstance(raw_moves, list) or not isinstance(raw_metrics, list):
        raise TypeError("Moves và move_metrics phải là danh sách.")

    rows = int(config["rows"])
    cols = int(config["cols"])
    win_length = int(config["win_length"])
    if not (3 <= rows <= 20 and 3 <= cols <= 24):
        raise ValueError("Kích thước bàn trong lịch sử không hợp lệ.")
    if not 3 <= win_length <= min(8, rows, cols):
        raise ValueError("Điều kiện thắng trong lịch sử không hợp lệ.")

    moves = tuple(
        Move(
            row=int(move["row"]),
            col=int(move["col"]),
            player=int(move["player"]),
            number=int(move["number"]),
        )
        for move in raw_moves
    )
    for move in moves:
        if move.player not in (PLAYER_X, PLAYER_O):
            raise ValueError("Player trong lịch sử không hợp lệ.")
        if not (0 <= move.row < rows and 0 <= move.col < cols):
            raise ValueError("Tọa độ nước đi trong lịch sử không hợp lệ.")

    move_metrics = tuple(_move_metric_from_dict(metric) for metric in raw_metrics)
    record = MatchHistoryRecord(
        number=int(data["number"]),
        timestamp=str(data["timestamp"]),
        mode_label=str(labels["mode"]),
        board_label=str(labels["board"]),
        x_agent=str(labels["x_agent"]),
        o_agent=str(labels["o_agent"]),
        result=str(labels["result"]),
        move_count=int(totals["move_count"]),
        game_seed=int(data["game_seed"]),
        total_time_ms=float(totals["total_time_ms"]),
        total_nodes=int(totals["total_nodes"]),
        total_pruned=int(totals["total_pruned"]),
        ai_move_count=int(totals["ai_move_count"]),
        rows=rows,
        cols=cols,
        win_length=win_length,
        match_mode=str(config["match_mode"]),
        ai_x_key=str(config["ai_x"]),
        ai_o_key=str(config["ai_o"]),
        winner=int(result["winner"]),
        is_draw=bool(result["is_draw"]),
        moves=moves,
        move_metrics=move_metrics,
    )
    if record.move_count != len(record.moves):
        raise ValueError("Move count không khớp dữ liệu replay.")
    state = record.build_state()
    if not state.game_over:
        raise ValueError("Lịch sử chỉ nhận trận đã kết thúc.")
    if state.winner != record.winner or state.is_draw != record.is_draw:
        raise ValueError("Kết quả replay không khớp summary.")
    valid_numbers = {move.number for move in record.moves}
    if any(metric.move_number not in valid_numbers for metric in record.move_metrics):
        raise ValueError("Metric tham chiếu nước đi không tồn tại.")
    return record
