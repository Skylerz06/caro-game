"""Hiển thị bàn cờ và chuyển đổi tọa độ chuột thành ô cờ."""

from __future__ import annotations

import pygame

from config.settings import COLORS, GameSettings
from game.board import EMPTY, PLAYER_O, PLAYER_X
from game.state import GameState
from ui.components import draw_panel, draw_text
from utils.helpers import player_label


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

    def draw(
        self,
        surface: pygame.Surface,
        state: GameState,
        settings: GameSettings,
        review_index: int,
        result_notice_started_at: int,
        result_notice_ms: int,
    ) -> None:
        """Vẽ trạng thái bàn cờ trực tiếp hoặc tại một mốc lịch sử."""
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

        notice_age = pygame.time.get_ticks() - result_notice_started_at
        show_result_notice = (
            state.game_over
            and review_index == len(state.history)
            and (result_notice_started_at == 0 or notice_age <= result_notice_ms)
        )
        if show_result_notice:
            self._draw_result_notice(surface, state)

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
