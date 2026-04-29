import pygame

SCREEN_W, SCREEN_H = 1280, 720


class MainMenu:
    """Màn hình chính: tiêu đề + nút Start."""

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self) -> None:
        # Vẽ tiêu đề "RUNE CRAFT" ở giữa màn hình
        # Vẽ "Nhấn ENTER để bắt đầu" phía dưới
        pass

    def handle_event(self, event: pygame.event.Event) -> str | None:
        # ENTER / SPACE → trả về 'start'
        # QUIT → trả về 'quit'
        pass
