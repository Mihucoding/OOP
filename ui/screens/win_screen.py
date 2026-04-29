import pygame

SCREEN_W, SCREEN_H = 1280, 720


class WinScreen:
    def __init__(self, screen, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, time_survived: float) -> None:
        # "CHIẾN THẮNG!" lớn ở giữa màu vàng
        # "Boss đã bị tiêu diệt!" + thời gian
        # "R để chơi lại / ESC thoát"
        pass

    def handle_event(self, event) -> str | None:
        # R → 'restart', ESC → 'quit'
        pass
