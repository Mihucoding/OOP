import pygame

SCREEN_W, SCREEN_H = 1280, 720


class GameOverScreen:
    def __init__(self, screen, font_big, font_small):
<<<<<<< HEAD
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

    def draw(self, wave: int, time_survived: float) -> None:
        self.screen.fill((15, 0, 0))

        # Tiêu đề
        title      = self.font_big.render("GAME  OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 100))
        self.screen.blit(title, title_rect)

        # Thống kê
        mins = int(time_survived) // 60
        secs = int(time_survived) % 60

        lines = [
            (f"Wave reached: {wave}",         (200, 200, 200)),
            (f"Time survived: {mins}:{secs:02d}", (200, 200, 200)),
        ]
        for i, (text, color) in enumerate(lines):
            surf = self.font_small.render(text, True, color)
            rect = surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + i * 36))
            self.screen.blit(surf, rect)

        # Gợi ý
        hint      = self.font_small.render("R - Restart     ESC - Quit", True, (130, 130, 130))
        hint_rect = hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 110))
        self.screen.blit(hint, hint_rect)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return 'restart'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        return None
=======
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
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
