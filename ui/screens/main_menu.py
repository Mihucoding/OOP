import pygame

SCREEN_W, SCREEN_H = 1280, 720


class MainMenu:
    """Màn hình chính: tiêu đề + chọn chế độ (Normal / Creative)."""

    # (key trả về, tiêu đề, mô tả)
    MODES = [
        ('start_normal',   "NORMAL",              "Chơi bình thường — sinh tồn qua các wave, hạ Boss."),
        ('start_creative', "CREATIVE  (Test)",    "Sandbox: tự spawn quái, nạp tổ hợp rune để soi bug."),
    ]

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small
        self.selected   = 0           # index trong MODES
        self._rects: list[pygame.Rect] = []

    def draw(self) -> None:
        self.screen.fill((15, 15, 25))

        # Tiêu đề
        title      = self.font_big.render("RUNE  CRAFT", True, (255, 200, 50))
        title_rect = title.get_rect(center=(SCREEN_W // 2, 150))
        self.screen.blit(title, title_rect)

        sub      = self.font_small.render("2D Survival Roguelike", True, (160, 160, 160))
        sub_rect = sub.get_rect(center=(SCREEN_W // 2, 200))
        self.screen.blit(sub, sub_rect)

        # Hai ô chọn chế độ
        self._rects = []
        box_w, box_h = 560, 96
        gap = 26
        total_h = len(self.MODES) * box_h + (len(self.MODES) - 1) * gap
        start_y = 300
        for i, (_key, name, desc) in enumerate(self.MODES):
            rect = pygame.Rect(SCREEN_W // 2 - box_w // 2,
                               start_y + i * (box_h + gap), box_w, box_h)
            self._rects.append(rect)
            picked = (i == self.selected)

            bg  = (30, 40, 62) if picked else (22, 24, 34)
            brd = (120, 200, 255) if picked else (70, 78, 96)
            pygame.draw.rect(self.screen, bg, rect, border_radius=12)
            pygame.draw.rect(self.screen, brd, rect, 3 if picked else 2, border_radius=12)

            # Số thứ tự
            num_col = (120, 200, 255) if picked else (110, 120, 140)
            num = self.font_big.render(str(i + 1), True, num_col)
            self.screen.blit(num, num.get_rect(midleft=(rect.left + 26, rect.centery)))

            name_col = (235, 245, 255) if picked else (170, 180, 195)
            name_surf = self.font_small.render(name, True, name_col)
            self.screen.blit(name_surf, (rect.left + 96, rect.top + 24))

            desc_surf = self.font_small.render(desc, True, (140, 150, 168))
            self.screen.blit(desc_surf, (rect.left + 96, rect.top + 54))

        # Gợi ý điều khiển menu
        hint = self.font_small.render(
            "↑ / ↓  hoặc  1 / 2  để chọn   —   ENTER để bắt đầu", True, (210, 210, 100))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, start_y + total_h + 46)))

        ctrl_lines = [
            "WASD di chuyển  ·  Chuột trái bắn  ·  Chuột phải ultimate",
            "Space lướt  ·  Q / E đổi chiêu  ·  Tab mở Rune Builder",
        ]
        for i, line in enumerate(ctrl_lines):
            surf = self.font_small.render(line, True, (120, 120, 120))
            rect = surf.get_rect(center=(SCREEN_W // 2, start_y + total_h + 92 + i * 26))
            self.screen.blit(surf, rect)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.QUIT:
            return 'quit'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'quit'
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.MODES)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.MODES)
            elif event.key == pygame.K_1:
                self.selected = 0
            elif event.key == pygame.K_2:
                self.selected = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.MODES[self.selected][0]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.MODES[i][0]
        return None
