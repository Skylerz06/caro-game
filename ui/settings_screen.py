"""Màn hình thay đổi luật chơi, chế độ và thuật toán AI."""

from __future__ import annotations

import pygame

from config.settings import (
    ALGORITHM_LABELS,
    ALGORITHMS,
    COLORS,
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


class SettingsScreen:
    def __init__(self) -> None:
        self.draft = GameSettings()
        self.focus_ai = False
        self.rows_stepper: Stepper
        self.cols_stepper: Stepper
        self.win_stepper: Stepper
        self.minimax_depth_stepper: Stepper
        self.alphabeta_depth_stepper: Stepper
        self.mode_selector: ChoiceSelector
        self.ai_x_selector: ChoiceSelector
        self.ai_o_selector: ChoiceSelector
        self.save_button = Button(
            pygame.Rect(850, 665, 250, 48), "LƯU CẤU HÌNH", accent=True
        )
        self.back_button = Button(
            pygame.Rect(155, 665, 170, 48), "QUAY LẠI"
        )
        self.default_button = Button(
            pygame.Rect(340, 665, 190, 48), "MẶC ĐỊNH"
        )
        self.open(GameSettings())

    def open(self, settings: GameSettings, focus_ai: bool = False) -> None:
        self.draft = GameSettings.from_dict(settings.to_dict())
        self.focus_ai = focus_ai

        self.rows_stepper = Stepper(
            pygame.Rect(165, 185, 410, 82),
            "SỐ HÀNG (m)",
            self.draft.rows,
            3,
            20,
        )
        self.cols_stepper = Stepper(
            pygame.Rect(165, 286, 410, 82),
            "SỐ CỘT (n)",
            self.draft.cols,
            3,
            24,
        )
        self.win_stepper = Stepper(
            pygame.Rect(165, 387, 410, 82),
            "ĐỘ DÀI THẮNG (k)",
            self.draft.win_length,
            3,
            min(8, self.draft.rows, self.draft.cols),
        )
        self.mode_selector = ChoiceSelector(
            pygame.Rect(650, 185, 450, 82),
            "CHẾ ĐỘ TRẬN ĐẤU",
            [(key, MATCH_MODE_LABELS[key]) for key in MATCH_MODES],
            self.draft.match_mode,
        )
        algorithm_options = [
            (key, ALGORITHM_LABELS[key]) for key in ALGORITHMS
        ]
        self.ai_x_selector = ChoiceSelector(
            pygame.Rect(650, 286, 450, 82),
            "THUẬT TOÁN CHO X",
            algorithm_options,
            self.draft.ai_x,
        )
        self.ai_o_selector = ChoiceSelector(
            pygame.Rect(650, 387, 450, 82),
            "THUẬT TOÁN CHO O",
            algorithm_options,
            self.draft.ai_o,
        )
        self.minimax_depth_stepper = Stepper(
            pygame.Rect(650, 488, 215, 82),
            "ĐỘ SÂU MINIMAX",
            self.draft.minimax_depth,
            1,
            4,
            " ply",
        )
        self.alphabeta_depth_stepper = Stepper(
            pygame.Rect(885, 488, 215, 82),
            "ĐỘ SÂU ALPHA-BETA",
            self.draft.alphabeta_depth,
            1,
            4,
            " ply",
        )
        self._update_enabled_controls()

    def _update_enabled_controls(self) -> None:
        mode = self.mode_selector.selected
        self.ai_x_selector.enabled = mode == "ai_ai"
        self.ai_o_selector.enabled = mode in ("human_ai", "ai_ai")

    def _sync_draft(self) -> None:
        self.draft.rows = self.rows_stepper.value
        self.draft.cols = self.cols_stepper.value
        self.win_stepper.maximum = min(
            8, self.draft.rows, self.draft.cols
        )
        self.win_stepper.value = min(
            self.win_stepper.value, self.win_stepper.maximum
        )
        self.draft.win_length = self.win_stepper.value
        self.draft.match_mode = self.mode_selector.selected
        self.draft.ai_x = self.ai_x_selector.selected
        self.draft.ai_o = self.ai_o_selector.selected
        self.draft.minimax_depth = self.minimax_depth_stepper.value
        self.draft.alphabeta_depth = self.alphabeta_depth_stepper.value
        self.draft.validate()
        self._update_enabled_controls()

    def handle_event(
        self, event: pygame.event.Event
    ) -> tuple[str, GameSettings | None] | None:
        if self.back_button.handle_event(event):
            return "back", None
        if self.default_button.handle_event(event):
            self.open(GameSettings(), self.focus_ai)
            return None
        if self.save_button.handle_event(event):
            self._sync_draft()
            return "save", GameSettings.from_dict(self.draft.to_dict())

        changed = False
        for control in (
            self.rows_stepper,
            self.cols_stepper,
            self.win_stepper,
            self.minimax_depth_stepper,
            self.alphabeta_depth_stepper,
            self.mode_selector,
            self.ai_x_selector,
            self.ai_o_selector,
        ):
            changed = control.handle_event(event) or changed
        if changed:
            self._sync_draft()
        return None

    def update(self) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        draw_gradient(
            surface, COLORS["background"], COLORS["background_2"]
        )
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

        panel = pygame.Rect(120, 120, 1040, 620)
        border = COLORS["primary"] if self.focus_ai else (48, 69, 101)
        draw_panel(
            surface,
            panel,
            COLORS["panel"],
            border_color=border,
        )

        draw_text(
            surface,
            "LUẬT CHƠI",
            18,
            COLORS["accent"],
            (165, 145),
            bold=True,
        )
        draw_text(
            surface,
            "CHẾ ĐỘ & AI",
            18,
            COLORS["primary"],
            (650, 145),
            bold=True,
        )

        self.rows_stepper.draw(surface)
        self.cols_stepper.draw(surface)
        self.win_stepper.draw(surface)
        self.mode_selector.draw(surface)
        self.ai_x_selector.draw(surface)
        self.ai_o_selector.draw(surface)
        self.minimax_depth_stepper.draw(surface)
        self.alphabeta_depth_stepper.draw(surface)

        draw_text(
            surface,
            "Kích thước hợp lệ: 3-20 hàng, 3-24 cột, k từ 3-8.",
            13,
            COLORS["muted"],
            (165, 500),
        )
        draw_text(
            surface,
            "Trong Người vs AI, người chơi cầm X và đi trước.",
            13,
            COLORS["muted"],
            (165, 526),
        )
        draw_text(
            surface,
            "Depth được cấu hình riêng cho từng thuật toán; Greedy cố định 1 ply.",
            13,
            COLORS["muted"],
            (650, 596),
        )

        self.back_button.draw(surface)
        self.default_button.draw(surface)
        self.save_button.draw(surface)
