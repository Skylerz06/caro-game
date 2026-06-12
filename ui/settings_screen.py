"""Man hinh thay doi luat choi, che do va thuat toan AI."""

from __future__ import annotations

import pygame

from config.settings import (
    ALGORITHM_LABELS,
    ALGORITHMS,
    COLORS,
    HUMAN_AI_FIRST_LABELS,
    HUMAN_AI_FIRST_OPTIONS,
    MATCH_MODE_LABELS,
    MATCH_MODES,
    GameSettings,
)
from ui.components import (
    Button,
    ChoiceSelector,
    Stepper,
    draw_gradient,
    draw_panel,
    draw_text,
)
from utils.helpers import branch_limit_for_depth


class SettingsScreen:
    def __init__(self) -> None:
        self.draft = GameSettings()
        self.steppers: dict[str, Stepper] = {}
        self.selectors: dict[str, ChoiceSelector] = {}
        self.controls: list[Stepper | ChoiceSelector] = []
        self.save_button = Button(
            pygame.Rect(850, 665, 250, 48), "LƯU CẤU HÌNH", accent=True
        )
        self.back_button = Button(pygame.Rect(155, 665, 170, 48), "QUAY LẠI")
        self.default_button = Button(pygame.Rect(340, 665, 190, 48), "MẶC ĐỊNH")
        self.open(GameSettings())

    def open(self, settings: GameSettings) -> None:
        self.draft = GameSettings.from_dict(settings.to_dict())
        stepper_specs = (
            ("rows", (165, 185, 410, 82), "SỐ HÀNG (m)", self.draft.rows, 3, 20, ""),
            ("cols", (165, 286, 410, 82), "SỐ CỘT (n)", self.draft.cols, 3, 24, ""),
            (
                "win",
                (165, 387, 410, 82),
                "ĐỘ DÀI THẮNG (k)",
                self.draft.win_length,
                3,
                min(8, self.draft.rows, self.draft.cols),
                "",
            ),
            (
                "minimax_depth",
                (650, 488, 215, 82),
                "ĐỘ SÂU MINIMAX",
                self.draft.minimax_depth,
                1,
                4,
                " ply",
            ),
            (
                "alphabeta_depth",
                (885, 488, 215, 82),
                "ĐỘ SÂU ALPHA-BETA",
                self.draft.alphabeta_depth,
                1,
                4,
                " ply",
            ),
        )
        self.steppers = {
            name: Stepper(pygame.Rect(*rect), label, value, minimum, maximum, suffix)
            for name, rect, label, value, minimum, maximum, suffix in stepper_specs
        }
        algorithms = [(key, ALGORITHM_LABELS[key]) for key in ALGORITHMS]
        selector_specs = (
            (
                "mode",
                (650, 185, 450, 82),
                "CHẾ ĐỘ TRẬN ĐẤU",
                [(key, MATCH_MODE_LABELS[key]) for key in MATCH_MODES],
                self.draft.match_mode,
            ),
            (
                "ai_x",
                (650, 286, 450, 82),
                "THUẬT TOÁN CHO X",
                algorithms,
                self.draft.ai_x,
            ),
            (
                "ai_o",
                (650, 387, 450, 82),
                "THUẬT TOÁN CHO O",
                algorithms,
                self.draft.ai_o,
            ),
            (
                "human_ai_first",
                (165, 488, 410, 82),
                "BÊN ĐI TRƯỚC (NGƯỜI vs AI)",
                [(key, HUMAN_AI_FIRST_LABELS[key]) for key in HUMAN_AI_FIRST_OPTIONS],
                self.draft.human_ai_first,
            ),
        )
        self.selectors = {
            name: ChoiceSelector(pygame.Rect(*rect), label, options, selected)
            for name, rect, label, options, selected in selector_specs
        }
        self.controls = [
            self.steppers["rows"],
            self.steppers["cols"],
            self.steppers["win"],
            self.selectors["mode"],
            self.selectors["ai_x"],
            self.selectors["ai_o"],
            self.selectors["human_ai_first"],
            self.steppers["minimax_depth"],
            self.steppers["alphabeta_depth"],
        ]
        self._update_enabled_controls()

    def _update_enabled_controls(self) -> None:
        mode = self.selectors["mode"].selected
        self.selectors["human_ai_first"].enabled = mode == "human_ai"
        self.selectors["ai_x"].enabled = mode == "ai_ai"
        self.selectors["ai_o"].enabled = mode in ("human_ai", "ai_ai")

    def _sync_draft(self) -> None:
        steps, choices = self.steppers, self.selectors
        self.draft.rows = steps["rows"].value
        self.draft.cols = steps["cols"].value
        steps["win"].maximum = min(8, self.draft.rows, self.draft.cols)
        steps["win"].value = min(steps["win"].value, steps["win"].maximum)
        self.draft.win_length = steps["win"].value
        self.draft.match_mode = choices["mode"].selected
        self.draft.human_ai_first = choices["human_ai_first"].selected
        self.draft.ai_x = choices["ai_x"].selected
        self.draft.ai_o = choices["ai_o"].selected
        self.draft.minimax_depth = steps["minimax_depth"].value
        self.draft.alphabeta_depth = steps["alphabeta_depth"].value
        self.draft.validate()
        self._update_enabled_controls()

    def handle_event(
        self, event: pygame.event.Event
    ) -> tuple[str, GameSettings | None] | None:
        if self.back_button.handle_event(event):
            return "back", None
        if self.default_button.handle_event(event):
            self.open(GameSettings())
            return None
        if self.save_button.handle_event(event):
            self._sync_draft()
            return "save", GameSettings.from_dict(self.draft.to_dict())
        if any(control.handle_event(event) for control in self.controls):
            self._sync_draft()
        return None

    def update(self) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(surface, COLORS["background"], COLORS["background_2"])
        draw_text(
            surface,
            "CẤU HÌNH TRÒ CHƠI",
            36,
            COLORS["text"],
            (640, 36),
            bold=True,
            anchor="midtop",
        )
        draw_text(
            surface,
            "Thiết lập luật m,n,k và tác nhân tìm kiếm",
            15,
            COLORS["muted"],
            (640, 82),
            anchor="midtop",
        )
        draw_panel(
            surface,
            pygame.Rect(120, 120, 1040, 620),
            COLORS["panel"],
            border_color=(48, 69, 101),
        )
        draw_text(surface, "LUẬT CHƠI", 18, COLORS["accent"], (165, 145), bold=True)
        draw_text(surface, "CHẾ ĐỘ & AI", 18, COLORS["primary"], (650, 145), bold=True)
        for control in self.controls:
            control.draw(surface)
        for key, center_x in (
            ("minimax_depth", 757),
            ("alphabeta_depth", 992),
        ):
            limit = branch_limit_for_depth(self.steppers[key].value)
            draw_text(
                surface,
                f"Giới hạn nhánh: {limit} ứng viên/nút",
                12,
                COLORS["primary"],
                (center_x, 578),
                bold=True,
                anchor="midtop",
            )
        notes = (
            ("Người luôn cầm X, AI luôn cầm O; có thể chọn O đi trước.", (165, 586)),
            ("Kích thước hợp lệ: 3-20 hàng, 3-24 cột, k từ 3-8.", (165, 612)),
            (
                "Depth được cấu hình riêng cho từng thuật toán; Greedy cố định 1 ply.",
                (650, 608),
            ),
        )
        for text, position in notes:
            draw_text(surface, text, 13, COLORS["muted"], position)
        for button in (self.back_button, self.default_button, self.save_button):
            button.draw(surface)
