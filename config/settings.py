"""Đọc, kiểm tra và lưu cấu hình của trò chơi."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SETTINGS_FILE = ROOT_DIR / "utils" / "settings.json"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 60
WINDOW_TITLE = "Caro Game"

ALGORITHMS = ("greedy", "minimax", "alphabeta")
ALGORITHM_LABELS = {
    "greedy": "Greedy Search",
    "minimax": "Minimax",
    "alphabeta": "Alpha-Beta",
}

MATCH_MODES = ("human_human", "human_ai", "ai_ai")
MATCH_MODE_LABELS = {
    "human_human": "Người vs Người",
    "human_ai": "Người vs AI",
    "ai_ai": "AI vs AI",
}

# Bảng màu thống nhất cho toàn bộ giao diện.
COLORS = {
    "background": (15, 23, 42),
    "background_2": (24, 35, 58),
    "panel": (28, 41, 66),
    "panel_light": (37, 52, 80),
    "primary": (55, 189, 248),
    "primary_dark": (14, 116, 144),
    "accent": (251, 146, 60),
    "danger": (248, 113, 113),
    "success": (74, 222, 128),
    "text": (241, 245, 249),
    "muted": (148, 163, 184),
    "board": (241, 229, 200),
    "board_line": (102, 83, 57),
    "x": (239, 68, 68),
    "o": (37, 99, 235),
    "white": (255, 255, 255),
    "black": (17, 24, 39),
}


@dataclass
class GameSettings:
    """Cấu hình có thể thay đổi từ màn hình Settings."""

    rows: int = 15
    cols: int = 15
    win_length: int = 5
    match_mode: str = "human_ai"
    ai_x: str = "minimax"
    ai_o: str = "alphabeta"
    minimax_depth: int = 2
    alphabeta_depth: int = 2
    ai_delay_ms: int = 350

    def validate(self) -> "GameSettings":
        """Chuẩn hóa dữ liệu để tránh cấu hình không hợp lệ."""
        self.rows = max(3, min(20, int(self.rows)))
        self.cols = max(3, min(24, int(self.cols)))
        max_win = min(8, self.rows, self.cols)
        self.win_length = max(3, min(max_win, int(self.win_length)))
        self.minimax_depth = max(1, min(4, int(self.minimax_depth)))
        self.alphabeta_depth = max(1, min(4, int(self.alphabeta_depth)))
        self.ai_delay_ms = max(0, min(2000, int(self.ai_delay_ms)))

        if self.match_mode not in MATCH_MODES:
            self.match_mode = "human_ai"
        if self.ai_x not in ALGORITHMS:
            self.ai_x = "minimax"
        if self.ai_o not in ALGORITHMS:
            self.ai_o = "alphabeta"
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameSettings":
        """Chỉ nhận các khóa đã biết để tương thích với file cũ."""
        allowed = cls.__dataclass_fields__.keys()
        values = {key: value for key, value in data.items() if key in allowed}
        legacy_depth = data.get("ai_depth")
        if legacy_depth is not None:
            values.setdefault("minimax_depth", legacy_depth)
            values.setdefault("alphabeta_depth", legacy_depth)
        try:
            return cls(**values).validate()
        except (TypeError, ValueError):
            return cls().validate()


def load_settings() -> GameSettings:
    """Đọc cấu hình; dùng mặc định nếu file thiếu hoặc hỏng."""
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return GameSettings.from_dict(data)
    except (OSError, json.JSONDecodeError, TypeError):
        settings = GameSettings()
        save_settings(settings)
        return settings


def save_settings(settings: GameSettings) -> None:
    """Lưu cấu hình dưới dạng JSON dễ đọc cho báo cáo/thử nghiệm."""
    settings.validate()
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
