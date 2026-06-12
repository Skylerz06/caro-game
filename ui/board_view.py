"""Hiển thị bàn cờ và trực quan hóa quyết định của AI."""

from __future__ import annotations

import pygame

from config.settings import COLORS, GameSettings
from game.board import EMPTY, PLAYER_O, PLAYER_X
from game.state import GameState, column_name
from ui.components import FontCache, draw_panel, draw_text
from utils.helpers import (
    CandidateScore,
    SearchAnalysis,
    format_search_score,
    player_label,
)


class BoardView:
    """Chịu trách nhiệm hình học và render bàn cờ."""

    PANEL_RECT = pygame.Rect(24, 90, 840, 620)
    AREA_RECT = pygame.Rect(42, 108, 804, 584)

    def geometry(self, settings: GameSettings) -> tuple[float, float, float]:
        """Tính gốc và kích thước ô theo số hàng/cột hiện tại."""
        cell_size = min(
            self.AREA_RECT.width / settings.cols,
            self.AREA_RECT.height / settings.rows,
        )
        width = cell_size * settings.cols
        height = cell_size * settings.rows
        origin_x = self.AREA_RECT.centerx - width / 2
        origin_y = self.AREA_RECT.centery - height / 2
        return origin_x, origin_y, cell_size

    def cell_at(
        self,
        position: tuple[int, int],
        settings: GameSettings,
    ) -> tuple[int, int] | None:
        """Đổi tọa độ màn hình thành (row, col), hoặc None nếu ngoài bàn."""
        origin_x, origin_y, cell_size = self.geometry(settings)
        x, y = position
        board_width = cell_size * settings.cols
        board_height = cell_size * settings.rows
        if not (
            origin_x <= x < origin_x + board_width
            and origin_y <= y < origin_y + board_height
        ):
            return None

        col = int((x - origin_x) // cell_size)
        row = int((y - origin_y) // cell_size)
        return row, col

    @staticmethod
    def _draw_piece(
        surface: pygame.Surface,
        player: int,
        center: tuple[int, int],
        cell_size: float,
    ) -> None:
        radius = max(6, int(cell_size * 0.30))
        width = max(2, int(cell_size * 0.09))
        if player == PLAYER_X:
            offset = int(radius * 0.75)
            pygame.draw.line(
                surface,
                COLORS["x"],
                (center[0] - offset, center[1] - offset),
                (center[0] + offset, center[1] + offset),
                width,
            )
            pygame.draw.line(
                surface,
                COLORS["x"],
                (center[0] + offset, center[1] - offset),
                (center[0] - offset, center[1] + offset),
                width,
            )
        elif player == PLAYER_O:
            pygame.draw.circle(surface, COLORS["o"], center, radius, width)

    @staticmethod
    def _heat_color(candidate: CandidateScore, total: int) -> tuple[int, int, int]:
        """Đổi thứ hạng thành dải xanh-vàng-đỏ ổn định với mọi thang điểm."""
        ratio = 0.0 if total <= 1 else (candidate.rank - 1) / (total - 1)
        green = COLORS["success"]
        yellow = (250, 204, 21)
        red = COLORS["danger"]
        if ratio <= 0.5:
            local_ratio = ratio * 2
            start, end = green, yellow
        else:
            local_ratio = (ratio - 0.5) * 2
            start, end = yellow, red
        return tuple(
            round(start_value + (end_value - start_value) * local_ratio)
            for start_value, end_value in zip(start, end)
        )

    @staticmethod
    def _blend_color(
        base: tuple[int, int, int],
        overlay: tuple[int, int, int],
        strength: float = 0.46,
    ) -> tuple[int, int, int]:
        return tuple(
            round(base_value * (1 - strength) + overlay_value * strength)
            for base_value, overlay_value in zip(base, overlay)
        )

    def draw(
        self,
        surface: pygame.Surface,
        state: GameState,
        settings: GameSettings,
        review_index: int,
        result_notice_started_at: int,
        result_notice_ms: int,
        *,
        show_analysis: bool = False,
        analysis: SearchAnalysis | None = None,
        mouse_position: tuple[int, int] | None = None,
        show_result_notice: bool = True,
    ) -> None:
        """Vẽ bàn cờ trực tiếp hoặc tại một mốc lịch sử."""
        draw_panel(
            surface,
            self.PANEL_RECT,
            COLORS["panel"],
            border_color=(48, 69, 101),
        )
        board = (
            state.board
            if review_index == len(state.history)
            else state.board_at(review_index)
        )
        origin_x, origin_y, cell_size = self.geometry(settings)
        board_rect = pygame.Rect(
            round(origin_x),
            round(origin_y),
            round(cell_size * settings.cols),
            round(cell_size * settings.rows),
        )
        pygame.draw.rect(surface, COLORS["board"], board_rect, border_radius=10)

        winning = (
            set(state.winning_line) if review_index == len(state.history) else set()
        )
        last_move = state.history[review_index - 1] if review_index > 0 else None
        candidates = (
            {(item.row, item.col): item for item in analysis.candidates}
            if show_analysis and analysis is not None
            else {}
        )
        candidate_total = len(candidates)

        for row in range(settings.rows):
            for col in range(settings.cols):
                left = origin_x + col * cell_size
                top = origin_y + row * cell_size
                cell_rect = pygame.Rect(
                    round(left),
                    round(top),
                    max(1, round(cell_size)),
                    max(1, round(cell_size)),
                )
                candidate = candidates.get((row, col))
                if candidate is not None:
                    color = self._heat_color(candidate, candidate_total)
                    pygame.draw.rect(
                        surface,
                        self._blend_color(COLORS["board"], color),
                        cell_rect,
                    )
                if (row, col) in winning:
                    pygame.draw.rect(surface, (187, 247, 208), cell_rect)
                pygame.draw.rect(
                    surface,
                    COLORS["board_line"],
                    cell_rect,
                    width=1,
                )

                player = board[row][col]
                if player != EMPTY:
                    center = (
                        round(left + cell_size / 2),
                        round(top + cell_size / 2),
                    )
                    self._draw_piece(surface, player, center, cell_size)
                    if last_move and last_move.row == row and last_move.col == col:
                        pygame.draw.circle(
                            surface,
                            COLORS["accent"],
                            center,
                            max(2, int(cell_size * 0.07)),
                        )
                if candidate is not None and candidate.selected:
                    pygame.draw.rect(
                        surface,
                        COLORS["accent"],
                        cell_rect.inflate(-2, -2),
                        width=max(2, round(cell_size * 0.08)),
                    )

        if show_analysis:
            self._draw_analysis_status(surface, board_rect, analysis)

        notice_age = pygame.time.get_ticks() - result_notice_started_at
        show_result_notice = show_result_notice and (
            state.game_over
            and review_index == len(state.history)
            and (result_notice_started_at == 0 or notice_age <= result_notice_ms)
        )
        if show_result_notice:
            self._draw_result_notice(surface, state)

        if show_analysis and analysis is not None:
            self._draw_analysis_tooltip(
                surface,
                settings,
                analysis,
                (
                    mouse_position
                    if mouse_position is not None
                    else pygame.mouse.get_pos()
                ),
            )

    def _draw_analysis_status(
        self,
        surface: pygame.Surface,
        board_rect: pygame.Rect,
        analysis: SearchAnalysis | None,
    ) -> None:
        text = (
            f"AI HEATMAP • {analysis.score_label} • {len(analysis.candidates)} ứng viên"
            if analysis is not None
            else "AI HEATMAP • Không có dữ liệu cho nước đang xem"
        )
        font = FontCache.get(11, True)
        text_image = font.render(text, True, COLORS["text"])
        badge = text_image.get_rect(
            bottomleft=(board_rect.left + 10, board_rect.bottom - 10)
        ).inflate(16, 10)
        pygame.draw.rect(surface, (15, 23, 42), badge, border_radius=7)
        surface.blit(text_image, text_image.get_rect(center=badge.center))

    def _draw_analysis_tooltip(
        self,
        surface: pygame.Surface,
        settings: GameSettings,
        analysis: SearchAnalysis,
        mouse_position: tuple[int, int],
    ) -> None:
        cell = self.cell_at(mouse_position, settings)
        if cell is None:
            return
        candidate = next(
            (item for item in analysis.candidates if (item.row, item.col) == cell),
            None,
        )
        if candidate is None:
            return

        notation = f"{column_name(candidate.col)}{candidate.row + 1}"
        lines = [
            f"{notation}  •  Rank #{candidate.rank}/{len(analysis.candidates)}",
            f"{analysis.score_label}: {format_search_score(candidate.score)}",
        ]
        details: list[str] = []
        if candidate.selected:
            details.append("Nước được chọn")
        if candidate.terminal_win:
            details.append("Thắng ngay")
        if candidate.pruned_branches:
            details.append(f"Pruned: {candidate.pruned_branches}")
        if details:
            lines.append("  •  ".join(details))

        fonts = [FontCache.get(13, True)] + [FontCache.get(12) for _ in lines[1:]]
        images = [
            font.render(line, True, COLORS["text"]) for font, line in zip(fonts, lines)
        ]
        width = max(image.get_width() for image in images) + 24
        height = (
            sum(image.get_height() for image in images) + 18 + 4 * (len(images) - 1)
        )
        left = min(mouse_position[0] + 16, surface.get_width() - width - 8)
        top = min(mouse_position[1] + 16, surface.get_height() - height - 8)
        left = max(8, left)
        top = max(8, top)
        tooltip = pygame.Rect(left, top, width, height)
        pygame.draw.rect(surface, COLORS["black"], tooltip, border_radius=9)
        pygame.draw.rect(
            surface,
            COLORS["primary"],
            tooltip,
            width=1,
            border_radius=9,
        )
        line_y = tooltip.top + 9
        for image in images:
            surface.blit(image, (tooltip.left + 12, line_y))
            line_y += image.get_height() + 4

    def _draw_result_notice(self, surface: pygame.Surface, state: GameState) -> None:
        overlay = pygame.Surface((430, 100), pygame.SRCALPHA)
        pygame.draw.rect(
            overlay,
            (15, 23, 42, 225),
            overlay.get_rect(),
            border_radius=18,
        )
        if state.is_draw:
            title = "VÁN ĐẤU HÒA"
            color = COLORS["accent"]
        else:
            title = f"NGƯỜI CHƠI {player_label(state.winner)} THẮNG"
            color = COLORS["success"]
        draw_text(
            overlay,
            title,
            24,
            color,
            (215, 24),
            bold=True,
            anchor="midtop",
        )
        draw_text(
            overlay,
            "Chọn CHƠI LẠI để bắt đầu ván mới",
            14,
            COLORS["text"],
            (215, 62),
            anchor="midtop",
        )
        surface.blit(
            overlay,
            (
                self.PANEL_RECT.centerx - 215,
                self.PANEL_RECT.centery - 50,
            ),
        )
