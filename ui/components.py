"""Component giao diện tái sử dụng cho các màn hình Pygame."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pygame

from config.settings import COLORS


class FontCache:
    """Cache font để tránh tạo lại font mỗi frame."""

    _fonts: ClassVar[dict[tuple[int, bool], pygame.font.Font]] = {}

    @classmethod
    def get(cls, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in cls._fonts:
            font_name = pygame.font.match_font("segoeui,arial,dejavusans", bold=bold)
            cls._fonts[key] = pygame.font.Font(font_name, size)
        return cls._fonts[key]


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    position: tuple[int, int],
    *,
    bold: bool = False,
    anchor: str = "topleft",
) -> pygame.Rect:
    image = FontCache.get(size, bold).render(str(text), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


class GradientCache:
    """Cache nền gradient theo kích thước và bảng màu."""

    _surfaces: ClassVar[dict[
        tuple[tuple[int, int], tuple[int, int, int], tuple[int, int, int]],
        pygame.Surface,
    ]] = {}

    @classmethod
    def get(
        cls,
        size: tuple[int, int],
        top_color: tuple[int, int, int],
        bottom_color: tuple[int, int, int],
    ) -> pygame.Surface:
        key = (size, top_color, bottom_color)
        if key not in cls._surfaces:
            width, height = size
            gradient = pygame.Surface(size)
            for y in range(0, height, 3):
                ratio = y / max(1, height - 1)
                color = tuple(
                    int(top + (bottom - top) * ratio)
                    for top, bottom in zip(top_color, bottom_color)
                )
                pygame.draw.rect(gradient, color, (0, y, width, 3))
            cls._surfaces[key] = gradient
        return cls._surfaces[key]

def draw_gradient(
    surface: pygame.Surface,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    """Vẽ nền chuyển màu từ cache thay vì dựng lại mỗi frame."""
    surface.blit(
        GradientCache.get(surface.get_size(), top_color, bottom_color),
        (0, 0),
    )


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    *,
    radius: int = 18,
    border_color: tuple[int, int, int] | None = None,
    shadow: bool = True,
) -> None:
    if shadow:
        shadow_rect = rect.move(0, 7)
        pygame.draw.rect(surface, (9, 15, 29), shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=1,
            border_radius=radius,
        )


def is_left_click(
    event: pygame.event.Event,
    rect: pygame.Rect | None = None,
) -> bool:
    """Kiểm tra sự kiện nhả chuột trái, tùy chọn giới hạn trong rect."""
    if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
        return False
    return rect is None or rect.collidepoint(event.pos)


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    accent: bool = False
    danger: bool = False
    enabled: bool = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        return self.enabled and is_left_click(event, self.rect)

    def draw(self, surface: pygame.Surface) -> None:
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        if not self.enabled:
            color = (51, 65, 85)
            text_color = (100, 116, 139)
        elif self.danger:
            color = (220, 38, 38) if hovered else (185, 28, 28)
            text_color = COLORS["white"]
        elif self.accent:
            color = (14, 165, 233) if hovered else COLORS["primary_dark"]
            text_color = COLORS["white"]
        else:
            color = COLORS["panel_light"] if not hovered else (51, 72, 106)
            text_color = COLORS["text"]

        shadow = self.rect.move(0, 4)
        pygame.draw.rect(surface, (10, 16, 30), shadow, border_radius=12)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        if hovered:
            pygame.draw.rect(
                surface,
                COLORS["primary"],
                self.rect,
                width=1,
                border_radius=12,
            )
        draw_text(
            surface,
            self.text,
            17,
            text_color,
            self.rect.center,
            bold=True,
            anchor="center",
        )


@dataclass
class IconButton:
    rect: pygame.Rect
    icon: str
    enabled: bool = True
    tooltip: str = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        return self.enabled and is_left_click(event, self.rect)

    def draw(self, surface: pygame.Surface) -> None:
        hovered = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        color = COLORS["panel_light"] if self.enabled else (43, 53, 70)
        if hovered:
            color = (51, 75, 110)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        icon_color = COLORS["text"] if self.enabled else (100, 116, 139)
        center_x, center_y = self.rect.center

        if self.icon in ("left", "right"):
            direction = -1 if self.icon == "left" else 1
            points = [
                (center_x - direction * 5, center_y - 9),
                (center_x + direction * 5, center_y),
                (center_x - direction * 5, center_y + 9),
            ]
            pygame.draw.lines(surface, icon_color, False, points, 3)
        elif self.icon == "gear":
            pygame.draw.circle(surface, icon_color, self.rect.center, 10, 3)
            pygame.draw.circle(surface, icon_color, self.rect.center, 3)
            for angle in range(0, 360, 45):
                vector = pygame.Vector2(0, -14).rotate(angle)
                end = (center_x + vector.x, center_y + vector.y)
                pygame.draw.line(surface, icon_color, self.rect.center, end, 3)

        if hovered and self.tooltip:
            image = FontCache.get(13).render(self.tooltip, True, COLORS["text"])
            tip_rect = image.get_rect(
                midtop=(self.rect.centerx, self.rect.bottom + 9)
            )
            background = tip_rect.inflate(14, 8)
            pygame.draw.rect(surface, COLORS["black"], background, border_radius=7)
            surface.blit(image, tip_rect)


class _ValueControl:
    """Khung dùng chung cho control có hai nút đổi giá trị."""

    value_size = 18

    def __init__(self, rect: pygame.Rect, label: str) -> None:
        self.rect = rect
        self.label = label
        self.enabled = True
        self.left_rect = pygame.Rect(rect.left + 12, rect.bottom - 42, 42, 32)
        self.right_rect = pygame.Rect(rect.right - 54, rect.bottom - 42, 42, 32)
        self._direction_buttons = (
            (IconButton(self.left_rect, "left"), -1),
            (IconButton(self.right_rect, "right"), 1),
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        for button, direction in self._direction_buttons:
            button.enabled = self.enabled
            if button.handle_event(event):
                return self._change(direction)
        return False

    def draw(self, surface: pygame.Surface) -> None:
        base = COLORS["panel_light"] if self.enabled else (38, 48, 65)
        pygame.draw.rect(surface, base, self.rect, border_radius=14)
        draw_text(
            surface,
            self.label,
            15,
            COLORS["muted"] if self.enabled else (85, 97, 116),
            (self.rect.left + 14, self.rect.top + 10),
            bold=True,
        )
        self._draw_controls(surface)
        draw_text(
            surface,
            self.value_text,
            self.value_size,
            COLORS["text"] if self.enabled else (100, 116, 139),
            (self.rect.centerx, self.left_rect.centery),
            bold=True,
            anchor="center",
        )

    def _draw_controls(self, surface: pygame.Surface) -> None:
        for button, _ in self._direction_buttons:
            button.enabled = self.enabled
            button.draw(surface)

    def _change(self, direction: int) -> bool:
        raise NotImplementedError

    @property
    def value_text(self) -> str:
        raise NotImplementedError


class Stepper(_ValueControl):
    """Control số nguyên dùng nút trừ và cộng."""

    value_size = 23

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        value: int,
        minimum: int,
        maximum: int,
        suffix: str = "",
    ) -> None:
        super().__init__(rect, label)
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.suffix = suffix

    def _change(self, direction: int) -> bool:
        old_value = self.value
        self.value = min(self.maximum, max(self.minimum, self.value + direction))
        return old_value != self.value

    @property
    def value_text(self) -> str:
        return f"{self.value}{self.suffix}"

    def _draw_controls(self, surface: pygame.Surface) -> None:
        for control_rect, symbol in (
            (self.left_rect, "-"),
            (self.right_rect, "+"),
        ):
            hovered = control_rect.collidepoint(pygame.mouse.get_pos())
            color = (57, 78, 110) if hovered else (45, 62, 91)
            pygame.draw.rect(surface, color, control_rect, border_radius=9)
            draw_text(
                surface,
                symbol,
                22,
                COLORS["text"],
                control_rect.center,
                bold=True,
                anchor="center",
            )


class ChoiceSelector(_ValueControl):
    """Control tuần tự qua lựa chọn bằng nút trái và phải."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        options: list[tuple[str, str]],
        selected: str,
    ) -> None:
        super().__init__(rect, label)
        self.options = options
        values = [value for value, _ in options]
        self.index = values.index(selected) if selected in values else 0

    @property
    def selected(self) -> str:
        return self.options[self.index][0]

    @selected.setter
    def selected(self, value: str) -> None:
        values = [option_value for option_value, _ in self.options]
        if value in values:
            self.index = values.index(value)

    @property
    def selected_label(self) -> str:
        return self.options[self.index][1]

    @property
    def value_text(self) -> str:
        return self.selected_label

    def _change(self, direction: int) -> bool:
        old_index = self.index
        self.index = (self.index + direction) % len(self.options)
        return old_index != self.index


def draw_metric_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    *,
    value_color: tuple[int, int, int] | None = None,
    note: str = "",
) -> None:
    pygame.draw.rect(surface, COLORS["panel_light"], rect, border_radius=13)
    draw_text(
        surface,
        label.upper(),
        12,
        COLORS["muted"],
        (rect.left + 14, rect.top + 10),
        bold=True,
    )
    draw_text(
        surface,
        value,
        20,
        value_color or COLORS["text"],
        (rect.left + 14, rect.top + 30),
        bold=True,
    )
    if note:
        draw_text(
            surface,
            note,
            11,
            COLORS["muted"],
            (rect.right - 12, rect.bottom - 10),
            anchor="bottomright",
        )
