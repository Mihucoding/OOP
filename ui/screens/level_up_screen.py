import pygame

SCREEN_W, SCREEN_H = 1280, 720


class LevelUpScreen:
    """
    Màn hình lên cấp: hiển thị 3 card mix Rune + StatUpgrade.
    Dừng game logic cho đến khi player chọn.
    """

    CARD_W   = 230
    CARD_H   = 310
    CARD_GAP = 40

    def __init__(self, screen: pygame.Surface, font_big, font_small):
        self.screen     = screen
        self.font_big   = font_big
        self.font_small = font_small

    def _card_rects(self, count: int):
        total_w = count * self.CARD_W + (count - 1) * self.CARD_GAP
        start_x = (SCREEN_W - total_w) // 2
        start_y = (SCREEN_H - self.CARD_H) // 2
        return [
            pygame.Rect(start_x + i * (self.CARD_W + self.CARD_GAP),
                        start_y, self.CARD_W, self.CARD_H)
            for i in range(count)
        ]

    def draw(self, choices: list) -> None:
        from logic.leveling.stat_upgrade import StatUpgrade

        # Overlay tối mờ nền
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        # Tiêu đề
        title      = self.font_big.render("LEVEL UP! - Choose a reward", True, (255, 220, 80))
        title_rect = title.get_rect(center=(SCREEN_W // 2,
                                            SCREEN_H // 2 - self.CARD_H // 2 - 54))
        self.screen.blit(title, title_rect)

        rects = self._card_rects(len(choices))
        for i, (choice, rect) in enumerate(zip(choices, rects)):
            if isinstance(choice, StatUpgrade):
                self._draw_stat_card(choice, rect, i)
            else:
                self._draw_rune_card(choice, rect, i)

        # Gợi ý phím
        hint = self.font_small.render("Press  1 / 2 / 3  or click a card",
                                      True, (160, 160, 160))
        hint_rect = hint.get_rect(
            center=(SCREEN_W // 2, SCREEN_H // 2 + self.CARD_H // 2 + 34))
        self.screen.blit(hint, hint_rect)

    # ── Rune card ──────────────────────────────────────────────────────────────

    def _draw_rune_card(self, rune, rect: pygame.Rect, idx: int) -> None:
        r, g, b = rune.get_color()

        # Nền card
        card_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        card_surf.fill((r // 5, g // 5, b // 5, 220))
        self.screen.blit(card_surf, rect.topleft)

        # Viền
        pygame.draw.rect(self.screen, (r, g, b), rect, 3, border_radius=10)

        # Badge loại
        badge_surf = self.font_small.render("RUNE", True, (r, g, b))
        self.screen.blit(badge_surf, (rect.x + 10, rect.y + 10))

        # Số phím
        num_surf = self.font_big.render(str(idx + 1), True, (255, 255, 255))
        self.screen.blit(num_surf, num_surf.get_rect(
            topright=(rect.right - 12, rect.y + 6)))

        # Icon vòng tròn màu
        pygame.draw.circle(self.screen, (r, g, b),
                           (rect.centerx, rect.y + 100), 28)
        abbr = self.font_big.render(rune.get_display_name()[:2], True, (0, 0, 0))
        self.screen.blit(abbr, abbr.get_rect(center=(rect.centerx, rect.y + 100)))

        # Tên rune
        name_surf = self.font_small.render(rune.get_display_name(), True, (r, g, b))
        self.screen.blit(name_surf, name_surf.get_rect(
            centerx=rect.centerx, y=rect.y + 142))

        # Mô tả
        desc = rune.get_description()
        desc_surf = self.font_small.render(desc, True, (210, 210, 210))
        if desc_surf.get_width() > rect.w - 16:
            ratio     = (rect.w - 16) / desc_surf.get_width()
            desc_surf = pygame.transform.smoothscale(
                desc_surf, (rect.w - 16, int(desc_surf.get_height() * ratio)))
        self.screen.blit(desc_surf, desc_surf.get_rect(
            centerx=rect.centerx, y=rect.y + 178))

    # ── Stat card ──────────────────────────────────────────────────────────────

    def _draw_stat_card(self, upgrade, rect: pygame.Rect, idx: int) -> None:
        r, g, b = upgrade.get_color()

        # Nền card
        card_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        card_surf.fill((r // 6, g // 6, b // 6, 220))
        self.screen.blit(card_surf, rect.topleft)

        # Viền rarity (dày hơn khi rarity cao)
        from logic.leveling.stat_upgrade import COMMON, UNCOMMON
        border_w = 2 if upgrade.rarity == COMMON else (
                   3 if upgrade.rarity == UNCOMMON else 4)
        pygame.draw.rect(self.screen, (r, g, b), rect, border_w, border_radius=10)

        # Badge "STAT"
        badge_surf = self.font_small.render("STAT", True, (r, g, b))
        self.screen.blit(badge_surf, (rect.x + 10, rect.y + 10))

        # Số phím
        num_surf = self.font_big.render(str(idx + 1), True, (255, 255, 255))
        self.screen.blit(num_surf, num_surf.get_rect(
            topright=(rect.right - 12, rect.y + 6)))

        # Rarity label
        rarity_surf = self.font_small.render(
            f"◆ {upgrade.get_rarity_label()}", True, (r, g, b))
        self.screen.blit(rarity_surf, rarity_surf.get_rect(
            centerx=rect.centerx, y=rect.y + 42))

        # Giá trị to ở giữa
        val_surf = self.font_big.render(upgrade.get_value_text(), True, (r, g, b))
        # Scale nhỏ lại nếu quá rộng
        if val_surf.get_width() > rect.w - 16:
            ratio    = (rect.w - 16) / val_surf.get_width()
            val_surf = pygame.transform.smoothscale(
                val_surf, (rect.w - 16, int(val_surf.get_height() * ratio)))
        self.screen.blit(val_surf, val_surf.get_rect(
            centerx=rect.centerx, y=rect.y + 110))

        # Tên stat
        name_surf = self.font_small.render(
            upgrade.get_display_name(), True, (220, 220, 220))
        self.screen.blit(name_surf, name_surf.get_rect(
            centerx=rect.centerx, y=rect.y + 178))

        # Dải màu rarity ở đáy card
        bar_rect = pygame.Rect(rect.x + 10, rect.bottom - 18,
                               rect.w - 20, 8)
        pygame.draw.rect(self.screen, (r, g, b), bar_rect, border_radius=4)

    # ── Event ──────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> int | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: return 0
            if event.key == pygame.K_2: return 1
            if event.key == pygame.K_3: return 2

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            rects  = self._card_rects(3)
            for i, rect in enumerate(rects):
                if rect.collidepoint(mx, my):
                    return i
        return None
