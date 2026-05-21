import pygame

SCREEN_W, SCREEN_H = 1280, 720


class MainMenu:
    """Màn hình chính: tiêu đề + nút Start."""

    def __init__(self, screen: pygame.Surface, font_big, font_small):
<<<<<<< HEAD
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

    def draw(self) -> None:
        self.screen.fill((15, 15, 25))

        # Tiêu đề
        title      = self.font_big.render("RUNE  CRAFT", True, (255, 200, 50))
        title_rect = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 70))
        self.screen.blit(title, title_rect)

        # Subtitle mô tả
        sub      = self.font_small.render("2D Survival Roguelike", True, (160, 160, 160))
        sub_rect = sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 10))
        self.screen.blit(sub, sub_rect)

        # Gợi ý bắt đầu (nhấp nháy không cần thiết — để đơn giản)
        hint      = self.font_small.render("Press  ENTER  or  SPACE  to start", True, (210, 210, 100))
        hint_rect = hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 50))
        self.screen.blit(hint, hint_rect)

        # Hướng dẫn điều khiển
        ctrl_lines = [
            "WASD - Move",
            "Left mouse - Shoot",
            "1 / 2 / 3 - Choose a reward when leveling up",
        ]
        for i, line in enumerate(ctrl_lines):
            surf = self.font_small.render(line, True, (120, 120, 120))
            rect = surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 110 + i * 26))
            self.screen.blit(surf, rect)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.QUIT:
            return 'quit'
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return 'start'
            if event.key == pygame.K_ESCAPE:
                return 'quit'
        return None
=======
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
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
