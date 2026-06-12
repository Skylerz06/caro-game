"""Điểm khởi động và bộ điều phối màn hình của Caro AI Lab."""

from __future__ import annotations

import os

# Ẩn thông báo chào của Pygame để terminal gọn hơn.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.history_store import MatchHistoryStore

from config.settings import (
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
    load_settings,
    save_settings,
)
from ui.game_screen import GameScreen
from ui.history_screen import HistoryScreen
from ui.menu import MenuScreen
from ui.replay_screen import ReplayScreen
from ui.settings_screen import SettingsScreen


class App:
    """Quản lý vòng lặp Pygame và chuyển đổi giữa các màn hình."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.settings = load_settings()
        self.history_store = MatchHistoryStore()
        self.match_history = self.history_store.load()
        self.menu_screen = MenuScreen()
        self.settings_screen = SettingsScreen()
        self.history_screen = HistoryScreen()
        self.replay_screen = ReplayScreen()
        self.game_screen = GameScreen(
            self.settings,
            self.match_history,
            self.history_store,
        )
        self.current_screen = "menu"
        self.settings_return_screen = "menu"
        self.history_return_screen = "menu"

    def _open_settings(self, return_screen: str, focus_ai: bool = False) -> None:
        self.settings_return_screen = return_screen
        self.settings_screen.open(self.settings, focus_ai)
        self.current_screen = "settings"

    def _open_history(self, return_screen: str) -> None:
        self.history_return_screen = return_screen
        self.history_screen.open(self.game_screen.match_history)
        self.current_screen = "history"

    def _handle_menu_action(self, action: str | None) -> None:
        if action == "play":
            self.game_screen.start(self.settings)
            self.current_screen = "game"
        elif action == "settings":
            self._open_settings("menu")
        elif action == "history":
            self._open_history("menu")
        elif action == "exit":
            self.running = False

    def _handle_settings_action(self, action) -> None:
        if action is None:
            return
        action_name, new_settings = action
        if action_name == "back":
            self.current_screen = self.settings_return_screen
        elif action_name == "save" and new_settings is not None:
            self.settings = new_settings
            save_settings(self.settings)
            if self.settings_return_screen == "game":
                # Thay đổi luật/AI bắt đầu một ván mới rõ ràng.
                self.game_screen.start(self.settings)
                self.current_screen = "game"
            else:
                self.current_screen = "menu"

    def _handle_game_action(self, action: str | None) -> None:
        if action == "menu":
            self.current_screen = "menu"
        elif action == "history":
            self._open_history("game")
        elif action == "settings":
            self._open_settings("game")

    def _handle_history_action(self, action) -> None:
        if action == "back":
            self.current_screen = self.history_return_screen
        elif isinstance(action, tuple) and action[0] == "replay":
            self.replay_screen.open(action[1])
            self.current_screen = "replay"

    def _handle_replay_action(self, action: str | None) -> None:
        if action == "back":
            self.current_screen = "history"

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            if self.current_screen == "menu":
                self.running = False
            elif self.current_screen == "settings":
                self.current_screen = self.settings_return_screen
            elif self.current_screen == "history":
                self.current_screen = self.history_return_screen
            elif self.current_screen == "replay":
                self.current_screen = "history"
            else:
                self.current_screen = "menu"
            return

        if self.current_screen == "menu":
            self._handle_menu_action(self.menu_screen.handle_event(event))
        elif self.current_screen == "settings":
            self._handle_settings_action(self.settings_screen.handle_event(event))
        elif self.current_screen == "history":
            self._handle_history_action(self.history_screen.handle_event(event))
        elif self.current_screen == "replay":
            self._handle_replay_action(self.replay_screen.handle_event(event))
        elif self.current_screen == "game":
            self._handle_game_action(self.game_screen.handle_event(event))

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self._handle_event(event)

            if self.current_screen == "menu":
                self.menu_screen.update()
                self.menu_screen.draw(self.surface)
            elif self.current_screen == "settings":
                self.settings_screen.update()
                self.settings_screen.draw(self.surface)
            elif self.current_screen == "history":
                self.history_screen.update()
                self.history_screen.draw(self.surface)
            elif self.current_screen == "replay":
                self.replay_screen.update()
                self.replay_screen.draw(self.surface)
            else:
                self.game_screen.update()
                self.game_screen.draw(self.surface)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
