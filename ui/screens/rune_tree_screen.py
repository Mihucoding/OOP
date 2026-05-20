import pygame

SCREEN_W, SCREEN_H = 1280, 720

NODE_RADIUS    = 36
LINE_COLOR     = (160, 160, 160)
EMPTY_COLOR    = (60, 60, 60)
EMPTY_BORDER   = (100, 100, 100)
TEXT_COLOR     = (255, 255, 255)
STACK_COLOR    = (255, 220, 80)
BG_OVERLAY     = (0, 0, 0, 200)


class RuneTreeScreen:
    """
    Màn hình Rune Builder — hiển thị cây Rune hiện tại dạng node graph.
    Mở bằng phím Tab trong lúc chơi, đóng bằng Tab hoặc ESC.

    Layout:
        Element node ở trên cùng (center)
        ↓
        Các Modifier gốc (parallel) — hàng ngang
        ↓
        Các Modifier con (serial) — hàng dưới từng nhánh
    """

    # Khoảng cách các tầng
    TIER_Y = [180, 330, 480]
    CARD_W = 320
    CARD_H = 200

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

    # ── Vẽ ────────────────────────────────────────────────────────────────────

    def draw(self, rune_tree) -> None:
        # Overlay tối
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(BG_OVERLAY)
        self.screen.blit(overlay, (0, 0))

        # Tiêu đề
        title      = self.font_big.render("CÂY RUNE", True, (255, 220, 50))
        title_rect = title.get_rect(center=(SCREEN_W // 2, 50))
        self.screen.blit(title, title_rect)

        hint = self.font_small.render("Tab / ESC — Đóng", True, (140, 140, 140))
        self.screen.blit(hint, (SCREEN_W - hint.get_width() - 16, 16))

        if not rune_tree.is_ready():
            # Chưa có Element nào
            msg  = self.font_small.render("Chưa có Rune nào. Hãy lên cấp để nhận Rune!", True, (160, 160, 160))
            self.screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
            return

        # ── Vẽ Element node ở tier 0 ──────────────────────────────────────────
        elem_x, elem_y = SCREEN_W // 2, self.TIER_Y[0]
        self._draw_node(rune_tree.element, elem_x, elem_y, is_element=True)

        # ── Vẽ Modifier nodes theo nhánh ──────────────────────────────────────
        mods = rune_tree.modifiers
        if not mods:
            msg = self.font_small.render("Chưa có Modifier. Hãy lên cấp thêm!", True, (120, 120, 120))
            self.screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, self.TIER_Y[1])))
            return

        # Tính vị trí ngang cho từng modifier gốc (spread đều)
        n_mods   = len(mods)
        spread_w = min(900, (n_mods - 1) * 240)
        if n_mods == 1:
            xs = [SCREEN_W // 2]
        else:
            xs = [
                SCREEN_W // 2 - spread_w // 2 + i * (spread_w // (n_mods - 1))
                for i in range(n_mods)
            ]

        for mod, mx in zip(mods, xs):
            my = self.TIER_Y[1]
            # Đường nối từ Element xuống Modifier
            pygame.draw.line(self.screen, LINE_COLOR, (elem_x, elem_y + NODE_RADIUS),
                             (mx, my - NODE_RADIUS), 2)
            self._draw_node(mod, mx, my)

            # Vẽ children (serial / depth 2)
            children = mod.get_children()
            if children:
                n_ch    = len(children)
                ch_xs   = [mx + (i - (n_ch - 1) / 2) * 160 for i in range(n_ch)]
                cy      = self.TIER_Y[2]
                for child, cx in zip(children, ch_xs):
                    pygame.draw.line(self.screen, LINE_COLOR,
                                     (mx, my + NODE_RADIUS), (cx, cy - NODE_RADIUS), 2)
                    self._draw_node(child, cx, cy)

                    # Depth 3
                    grand = child.get_children()
                    for gc in grand:
                        gcx = cx
                        gcy = cy + 150
                        pygame.draw.line(self.screen, LINE_COLOR,
                                         (cx, cy + NODE_RADIUS), (gcx, gcy - NODE_RADIUS), 2)
                        self._draw_node(gc, gcx, gcy)

        # ── Legenda ───────────────────────────────────────────────────────────
        self._draw_legend(rune_tree)

    def _draw_node(self, rune, x: int, y: int, is_element: bool = False) -> None:
        color  = rune.get_color()
        r, g, b = color

        # Vòng nền mờ
        glow_surf = pygame.Surface((NODE_RADIUS * 2 + 16, NODE_RADIUS * 2 + 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (r, g, b, 50),
                           (NODE_RADIUS + 8, NODE_RADIUS + 8), NODE_RADIUS + 8)
        self.screen.blit(glow_surf, (x - NODE_RADIUS - 8, y - NODE_RADIUS - 8))

        # Thân node
        border_color = (255, 255, 255) if is_element else (200, 200, 200)
        border_w     = 4 if is_element else 2
        pygame.draw.circle(self.screen, color, (x, y), NODE_RADIUS)
        pygame.draw.circle(self.screen, border_color, (x, y), NODE_RADIUS, border_w)

        # Tên rắn gọn (2 chữ cái đầu hoặc tên ngắn)
        abbr = rune.get_display_name()[:2]
        abbr_surf = self.font_big.render(abbr, True, (0, 0, 0))
        self.screen.blit(abbr_surf, abbr_surf.get_rect(center=(x, y)))

        # Tên đầy đủ bên dưới node
        name_surf = self.font_small.render(rune.get_display_name(), True, TEXT_COLOR)
        self.screen.blit(name_surf, name_surf.get_rect(center=(x, y + NODE_RADIUS + 16)))

        # Stack count (nếu có)
        stack = getattr(rune, 'element_stack', getattr(rune, 'stack', 1))
        if stack > 1:
            stk_surf = self.font_small.render(f"x{stack}", True, STACK_COLOR)
            self.screen.blit(stk_surf, (x + NODE_RADIUS - 6, y - NODE_RADIUS - 2))

    def _draw_legend(self, rune_tree) -> None:
        """Panel thông tin chi tiết ở góc dưới trái."""
        panel_x, panel_y = 20, SCREEN_H - 220
        panel_w, panel_h = 340, 200

        # Nền panel
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((20, 20, 30, 180))
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (80, 80, 80),
                         (panel_x, panel_y, panel_w, panel_h), 1)

        title = self.font_small.render("Chi tiet Rune:", True, (200, 200, 200))
        self.screen.blit(title, (panel_x + 10, panel_y + 8))

        y = panel_y + 34
        for rune in rune_tree.get_all_runes():
            stack = getattr(rune, 'element_stack', getattr(rune, 'stack', 1))
            label = f"  {rune.get_display_name()}"
            if stack > 1:
                label += f"  x{stack}"
            surf  = self.font_small.render(label, True, rune.get_color())
            self.screen.blit(surf, (panel_x + 10, y))
            desc  = self.font_small.render(f"    {rune.get_description()}", True, (140, 140, 140))
            # Scale nếu quá rộng
            if desc.get_width() > panel_w - 20:
                ratio = (panel_w - 20) / desc.get_width()
                desc  = pygame.transform.smoothscale(
                    desc, (panel_w - 20, int(desc.get_height() * ratio)))
            self.screen.blit(desc, (panel_x + 10, y + 18))
            y += 42
            if y > panel_y + panel_h - 20:
                break

    # ── Event ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Trả về True nếu muốn đóng màn hình này."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                return True
        return False
