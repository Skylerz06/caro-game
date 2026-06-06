"""Component giao diện tái sử dụng cho các màn hình Pygame."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from config.settings import COLORS


class FontCache:
    """Cache font để tránh tạo lại font mỗi frame."""

    _fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    @classmethod
    def get(cls, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in cls._fonts:
            font_name = pygame.font.match_font(
                "segoeui,arial,dejavusans", bold=bold
            )
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


def draw_gradient(
    surface: pygame.Surface,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    """Nền chuyển màu dọc, đủ nhẹ để vẽ mỗi frame."""
    width, height = surface.get_size()
    for y in range(0, height, 3):
        ratio = y / max(1, height - 1)
        color = tuple(
            int(top + (bottom - top) * ratio)
            for top, bottom in zip(top_color, bottom_color)
        )
        pygame.draw.rect(surface, color, (0, y, width, 3))


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
        pygame.draw.rect(
            surface, (9, 15, 29), shadow_rect, border_radius=radius
        )
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(
            surface,
            border_color,
            rect,
            width=1,
            border_radius=radius,
        )


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    accent: bool = False
    danger: bool = False
    enabled: bool = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        return bool(
            self.enabled
            and event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface: pygame.Surface) -> None:
        hovered = self.enabled and self.rect.collidepoint(
            pygame.mouse.get_pos()
        )
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
        return bool(
            self.enabled
            and event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface: pygame.Surface) -> None:
        hovered = self.enabled and self.rect.collidepoint(
            pygame.mouse.get_pos()
        )
        color = COLORS["panel_light"] if self.enabled else (43, 53, 70)
        if hovered:
            color = (51, 75, 110)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        icon_color = COLORS["text"] if self.enabled else (100, 116, 139)
        center = self.rect.center

        if self.icon == "left":
            points = [
                (center[0] + 5, center[1] - 9),
                (center[0] - 5, center[1]),
                (center[0] + 5, center[1] + 9),
            ]
            pygame.draw.lines(surface, icon_color, False, points, 3)
        elif self.icon == "right":
            points = [
                (center[0] - 5, center[1] - 9),
                (center[0] + 5, center[1]),
                (center[0] - 5, center[1] + 9),
            ]
            pygame.draw.lines(surface, icon_color, False, points, 3)
        elif self.icon == "gear":
            pygame.draw.circle(surface, icon_color, center, 10, 3)
            pygame.draw.circle(surface, icon_color, center, 3)
            for angle in range(0, 360, 45):
                vector = pygame.Vector2(0, -14).rotate(angle)
                end = (center[0] + vector.x, center[1] + vector.y)
                pygame.draw.line(surface, icon_color, center, end, 3)
        elif self.icon == "restart":
            pygame.draw.arc(
                surface,
                icon_color,
                self.rect.inflate(-17, -17),
                0.35,
                5.7,
                3,
            )
            pygame.draw.polygon(
                surface,
                icon_color,
                [
                    (center[0] - 12, center[1] - 7),
                    (center[0] - 3, center[1] - 10),
                    (center[0] - 5, center[1] - 1),
                ],
            )

        if hovered and self.tooltip:
            tip_rect = draw_text(
                surface,
                self.tooltip,
                13,
                COLORS["text"],
                (self.rect.centerx, self.rect.bottom + 9),
                anchor="midtop",
            )
            background = tip_rect.inflate(14, 8)
            pygame.draw.rect(
                surface, COLORS["black"], background, border_radius=7
            )
            surface.blit(
                FontCache.get(13).render(
                    self.tooltip, True, COLORS["text"]
                ),
                tip_rect,
            )


class Stepper:
    """Điều khiển số nguyên bằng nút trừ/cộng."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        value: int,
        minimum: int,
        maximum: int,
        suffix: str = "",
    ) -> None:
        self.rect = rect
        self.label = label
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.suffix = suffix
        self.minus_rect = pygame.Rect(
            rect.left + 12, rect.bottom - 42, 42, 32
        )
        self.plus_rect = pygame.Rect(
            rect.right - 54, rect.bottom - 42, 42, 32
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return False
        old_value = self.value
        if self.minus_rect.collidepoint(event.pos):
            self.value = max(self.minimum, self.value - 1)
        elif self.plus_rect.collidepoint(event.pos):
            self.value = min(self.maximum, self.value + 1)
        return old_value != self.value

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(
            surface, COLORS["panel_light"], self.rect, border_radius=14
        )
        draw_text(
            surface,
            self.label,
            15,
            COLORS["muted"],
            (self.rect.left + 14, self.rect.top + 10),
            bold=True,
        )
        for control_rect, symbol in (
            (self.minus_rect, "-"),
            (self.plus_rect, "+"),
        ):
            hovered = control_rect.collidepoint(pygame.mouse.get_pos())
            color = (57, 78, 110) if hovered else (45, 62, 91)
            pygame.draw.rect(
                surface, color, control_rect, border_radius=9
            )
            draw_text(
                surface,
                symbol,
                22,
                COLORS["text"],
                control_rect.center,
                bold=True,
                anchor="center",
            )
        value_text = f"{self.value}{self.suffix}"
        draw_text(
            surface,
            value_text,
            23,
            COLORS["text"],
            (self.rect.centerx, self.minus_rect.centery),
            bold=True,
            anchor="center",
        )


class ChoiceSelector:
    """Chọn một giá trị bằng hai mũi tên trái/phải."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        options: list[tuple[str, str]],
        selected: str,
    ) -> None:
        self.rect = rect
        self.label = label
        self.options = options
        self.enabled = True
        values = [value for value, _ in options]
        self.index = values.index(selected) if selected in values else 0
        self.left_rect = pygame.Rect(
            rect.left + 12, rect.bottom - 42, 42, 32
        )
        self.right_rect = pygame.Rect(
            rect.right - 54, rect.bottom - 42, 42, 32
        )

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

    def handle_event(self, event: pygame.event.Event) -> bool:
        if (
            not self.enabled
            or event.type != pygame.MOUSEBUTTONUP
            or event.button != 1
        ):
            return False
        old_index = self.index
        if self.left_rect.collidepoint(event.pos):
            self.index = (self.index - 1) % len(self.options)
        elif self.right_rect.collidepoint(event.pos):
            self.index = (self.index + 1) % len(self.options)
        return old_index != self.index

    def draw(self, surface: pygame.Surface) -> None:
        base = COLORS["panel_light"] if self.enabled else (38, 48, 65)
        pygame.draw.rect(surface, base, self.rect, border_radius=14)
        label_color = COLORS["muted"] if self.enabled else (85, 97, 116)
        draw_text(
            surface,
            self.label,
            15,
            label_color,
            (self.rect.left + 14, self.rect.top + 10),
            bold=True,
        )
        for control_rect, icon in (
            (self.left_rect, "left"),
            (self.right_rect, "right"),
        ):
            IconButton(control_rect, icon, self.enabled).draw(surface)
        draw_text(
            surface,
            self.selected_label,
            18,
            COLORS["text"] if self.enabled else (100, 116, 139),
            (self.rect.centerx, self.left_rect.centery),
            bold=True,
            anchor="center",
        )


def draw_metric_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    *,
    value_color: tuple[int, int, int] | None = None,
    note: str = "",
) -> None:
    pygame.draw.rect(
        surface, COLORS["panel_light"], rect, border_radius=13
    )
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

