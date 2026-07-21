"""
SkillSelectScreen — Màn chọn 2 hệ (skill) đầu ván.

Luồng: MainMenu → [Màn này: chọn đúng 2 hệ khác nhau] → Playing.

Tương tác:
  • Click crystal   → chọn/bỏ chọn (tối đa 2, phải khác nhau)
  • ENTER / nút OK  → xác nhận (chỉ khi đã đủ 2)
  • ESC             → thoát

handle_event trả về:
  • ('confirm', [key1, key2]) khi xác nhận đủ 2 hệ
  • 'quit' khi thoát
  • None còn lại
"""
import math
import os
import pygame

from ui import rune_ui_config as cfg

SCREEN_W, SCREEN_H = 1280, 720

CREST_R      = 66     # bán kính crystal
ROW_Y        = 300    # tâm hàng crystal
GAP          = 250    # khoảng cách giữa các crystal
CONFIRM_RECT = pygame.Rect(SCREEN_W // 2 - 130, 590, 260, 54)


class SkillSelectScreen:
    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small
        self.font_desc  = self._load_font(15)   # nhỏ hơn font_small — mô tả xuống dòng vừa cột crystal
        self.selected: list[str] = []   # key theo thứ tự chọn, tối đa 2
        self._time      = 0.0
        self._crests: list[tuple] = []  # (key, center, radius)

    def _load_font(self, size: int) -> pygame.font.Font:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        font_path = os.path.join(root_dir, "assets", "fonts", "pixel_font.ttf")
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            return pygame.font.SysFont(None, size)

    def reset(self) -> None:
        self.selected = []

    # ── Vẽ ─────────────────────────────────────────────────────────────────────

    def draw(self, dt: float = 0.0) -> None:
        self._time += dt
        self.screen.fill((8, 12, 24))
        self._draw_backdrop()

        title = self.font_big.render("CHOOSE  YOUR  2  ELEMENTS", True, (230, 244, 255))
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 120)))
        sub = self.font_small.render(
            "Pick 2 different elements — each becomes a spell (swap in-game with Q / E)",
            True, (130, 150, 175))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 160)))

        self._crests = []
        n = len(cfg.ELEMENT_ORDER)
        start_x = SCREEN_W // 2 - (n - 1) * GAP // 2
        for i, key in enumerate(cfg.ELEMENT_ORDER):
            center = (start_x + i * GAP, ROW_Y)
            self._crests.append((key, center, CREST_R))
            self._draw_crystal(key, center)

        self._draw_confirm()

    def _draw_backdrop(self) -> None:
        for i in range(8):
            a = 40 - i * 4
            if a <= 0:
                break
            pygame.draw.circle(self.screen, (24, 40, 70), (SCREEN_W // 2, ROW_Y),
                               520 - i * 46, 1)

    def _draw_crystal(self, key: str, center: tuple) -> None:
        th = cfg.theme(key)
        color = th["color"]
        picked = key in self.selected

        # Glow nhịp thở
        pulse = 0.5 + 0.5 * math.sin(self._time * 3.0 + hash(key) % 7)
        glow = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ga = (95 if picked else 45) + int(30 * pulse)
        pygame.draw.polygon(glow, (*color, ga),
                            self._hex(center, CREST_R + 10 + int(5 * pulse)))
        self.screen.blit(glow, (0, 0))

        # Thân crest
        pts = self._hex(center, CREST_R)
        pygame.draw.polygon(self.screen, self._shade(color, 0.55), pts)
        pygame.draw.polygon(self.screen, self._shade(color, 1.25), pts, 5 if picked else 3)

        # Icon hoặc glyph
        icon = cfg.element_icon(key)
        if icon is not None:
            size = int((CREST_R - 8) * 2)
            img = pygame.transform.smoothscale(icon, (size, size))
            self.screen.blit(img, img.get_rect(center=center))
        else:
            g = self.font_big.render(th["glyph"], True, (245, 255, 255))
            self.screen.blit(g, g.get_rect(center=center))

        # Badge số thứ tự khi được chọn
        if picked:
            idx = self.selected.index(key) + 1
            bx, by = center[0] + CREST_R - 6, center[1] - CREST_R + 6
            pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 15)
            pygame.draw.circle(self.screen, color, (bx, by), 15, 3)
            num = self.font_small.render(str(idx), True, (20, 28, 40))
            self.screen.blit(num, num.get_rect(center=(bx, by)))

        # Tên + mô tả (mô tả tự xuống dòng cho vừa bề rộng cột, tránh đè crystal kế bên)
        name = self.font_small.render(th["name"], True, color)
        self.screen.blit(name, name.get_rect(center=(center[0], center[1] + CREST_R + 26)))
        desc_lines = self._wrap_text(th["desc"], self.font_desc, GAP - 20)
        line_h = self.font_desc.get_height() + 2
        desc_y = center[1] + CREST_R + 50
        for i, line in enumerate(desc_lines):
            surf = self.font_desc.render(line, True, (170, 185, 205))
            self.screen.blit(surf, surf.get_rect(center=(center[0], desc_y + i * line_h)))

    def _draw_confirm(self) -> None:
        ready = len(self.selected) == 2
        col   = (90, 220, 150) if ready else (70, 80, 95)
        bg    = (18, 40, 32) if ready else (16, 20, 30)
        pygame.draw.rect(self.screen, bg, CONFIRM_RECT, border_radius=12)
        pygame.draw.rect(self.screen, col, CONFIRM_RECT, 3, border_radius=12)
        label = "START  (Enter)" if ready else f"Select {2 - len(self.selected)} more"
        txt = self.font_small.render(label, True, col if ready else (150, 160, 175))
        self.screen.blit(txt, txt.get_rect(center=CONFIRM_RECT.center))

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _hex(self, center: tuple, radius: int) -> list:
        cx, cy = center
        return [
            (int(cx + math.cos(math.radians(60 * i - 30)) * radius),
             int(cy + math.sin(math.radians(60 * i - 30)) * radius))
            for i in range(6)
        ]

    def _shade(self, color: tuple, scale: float) -> tuple:
        return tuple(max(0, min(255, int(c * scale))) for c in color)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list:
        """Cắt `text` thành nhiều dòng sao cho mỗi dòng render ra không quá
        `max_width` px — pygame không tự word-wrap nên phải tự làm bằng tay,
        gộp từng từ vào dòng hiện tại tới khi vượt bề rộng thì xuống dòng mới."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if not current or font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # ── Event ──────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            return 'quit'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'quit'
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and len(self.selected) == 2:
                return ('confirm', list(self.selected))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if CONFIRM_RECT.collidepoint(mx, my) and len(self.selected) == 2:
                return ('confirm', list(self.selected))
            for key, center, radius in self._crests:
                if math.hypot(mx - center[0], my - center[1]) <= radius:
                    self._toggle(key)
                    break
        return None

    def _toggle(self, key: str) -> None:
        if key in self.selected:
            self.selected.remove(key)
        elif len(self.selected) < 2:
            self.selected.append(key)
