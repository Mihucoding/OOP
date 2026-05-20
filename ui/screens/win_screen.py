import pygame

SCREEN_W, SCREEN_H = 1280, 720


class WinScreen:
    def __init__(self, screen, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

    def draw(self, time_survived: float) -> None:
        self.screen.fill((0, 15, 0))

        # Tiêu đề
        title      = self.font_big.render("CHIẾN  THẮNG!", True, (255, 220, 0))
        title_rect = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 100))
        self.screen.blit(title, title_rect)

        # Chi tiết
        mins = int(time_survived) // 60
        secs = int(time_survived) % 60

        lines = [
            ("Boss đã bị tiêu diệt!",              (180, 255, 120)),
            (f"Thời gian hoàn thành: {mins}:{secs:02d}", (200, 200, 200)),
        ]
        for i, (text, color) in enumerate(lines):
            surf = self.font_small.render(text, True, color)
            rect = surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + i * 36))
            self.screen.blit(surf, rect)

        # Gợi ý
        hint      = self.font_small.render("R — Chơi lại     ESC — Thoát", True, (130, 130, 130))
        hint_rect = hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 110))
        self.screen.blit(hint, hint_rect)

    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return 'restart'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        return None
