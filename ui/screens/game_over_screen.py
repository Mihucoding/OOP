import pygame

SCREEN_W, SCREEN_H = 1280, 720


class GameOverScreen:
    def __init__(self, screen, font_big, font_small):
        self.screen = screen
        self.font_big = font_big
        self.font_small = font_small

    def draw(self, wave: int, time_survived: float) -> None:
        # "GAME OVER" lớn ở giữa
        # "Wave đạt được: X" + "Thời gian: X:XX"
        # "R để chơi lại / ESC thoát"
        pass

    def handle_event(self, event) -> str | None:
        # R → 'restart', ESC → 'quit'
        pass
