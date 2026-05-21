import pygame

SCREEN_W, SCREEN_H = 1280, 720


class HUD:
    """Vẽ giao diện: HP bar, XP bar, level, wave, rune tree hiện tại."""

    BAR_X = 10
    BAR_Y = 10
    BAR_W = 220
    HP_H  = 20
    XP_H  = 14

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font   = font

    def draw(self, player, wave_info: str) -> None:
        # ── HP bar ────────────────────────────────────────────────────────────
        bar_x, bar_y = self.BAR_X, self.BAR_Y
        pygame.draw.rect(self.screen, (80, 0, 0),
                         (bar_x, bar_y, self.BAR_W, self.HP_H))
        hp_w = int(self.BAR_W * player.get_hp_ratio())
        if hp_w > 0:
            pygame.draw.rect(self.screen, (220, 40, 40),
                             (bar_x, bar_y, hp_w, self.HP_H))
        hp_text = self.font.render(
            f"HP  {int(player.hp)} / {player.max_hp}", True, (255, 255, 255))
        self.screen.blit(hp_text, (bar_x + 4, bar_y + 2))

        # ── XP bar ────────────────────────────────────────────────────────────
        xp_y = bar_y + self.HP_H + 6
        pygame.draw.rect(self.screen, (0, 60, 0),
                         (bar_x, xp_y, self.BAR_W, self.XP_H))
        xp_w = int(self.BAR_W * player.get_xp_ratio())
        if xp_w > 0:
            pygame.draw.rect(self.screen, (40, 200, 60),
                             (bar_x, xp_y, xp_w, self.XP_H))

        # Level kế bên XP bar
        lv_text = self.font.render(f"Lv.{player.level}", True, (190, 255, 160))
        self.screen.blit(lv_text, (bar_x + self.BAR_W + 8, xp_y - 2))

        # ── Wave (góc phải trên) ───────────────────────────────────────────────
        wave_surf = self.font.render(wave_info, True, (255, 220, 80))
        wave_rect = wave_surf.get_rect(topright=(SCREEN_W - 10, 10))
        self.screen.blit(wave_surf, wave_rect)

        # ── Stats cơ bản (armor / regen / xp_range) ──────────────────────────
        stats_y = xp_y + self.XP_H + 6
        if self._should_draw_overload(player):
            self._draw_overload_bar(player, stats_y)
            stats_y += 22
        self._draw_stats(player, stats_y)

        # ── Danh sách Rune của chiêu active ──────────────────────────────────
        rune_y    = stats_y + 44
        active_spell = player.get_active_spell()
        spell_surf = self.font.render(
            f"{active_spell.name}: {active_spell.rune_tree.describe()}",
            True, (180, 220, 255))
        self.screen.blit(spell_surf, (bar_x, rune_y))
        rune_y += 22

        all_runes = active_spell.rune_tree.get_all_runes()
        if not all_runes:
            hint = self.font.render("Tab: Open Rune Builder", True, (120, 120, 120))
            self.screen.blit(hint, (bar_x, rune_y))
        else:
            for rune in all_runes:
                stack = getattr(rune, 'stack', getattr(rune, 'element_stack', 1))
                label = rune.get_display_name()
                if stack > 1:
                    label += f"  x{stack}"
                surf = self.font.render(label, True, rune.get_color())
                self.screen.blit(surf, (bar_x, rune_y))
                rune_y += 22

        # ── Spell bar (bottom center) ─────────────────────────────────────────
        self._draw_spell_bar(player)

        # ── Notification: có rune mới trong inventory ─────────────────────────
        inv_count = len(player.rune_inventory)
        if inv_count > 0:
            notif_surf = self.font.render(
                f"[Tab] Open Rune Builder  ({inv_count} rune{'s' if inv_count != 1 else ''} available)",
                True, (255, 220, 50))
            notif_rect = notif_surf.get_rect(
                center=(SCREEN_W // 2, SCREEN_H - 95))
            bg = pygame.Surface(
                (notif_surf.get_width() + 20, notif_surf.get_height() + 8),
                pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            self.screen.blit(bg, (notif_rect.x - 10, notif_rect.y - 4))
            self.screen.blit(notif_surf, notif_rect)

    def _draw_cooldown_slot(self, x: int, y: int, h: int,
                            label: str, name: str,
                            timer: float, cooldown: float,
                            color: tuple) -> None:
        """Ô cooldown nhỏ: tên + thanh hồi chiêu."""
        W = 80
        r, g, b = color
        ready   = timer <= 0.0

        bg_col  = (30, 30, 40) if not ready else (20, 30, 20)
        bd_col  = color if ready else (60, 60, 70)
        pygame.draw.rect(self.screen, bg_col,
                         (x, y, W, h), border_radius=6)
        pygame.draw.rect(self.screen, bd_col,
                         (x, y, W, h), 2 if ready else 1, border_radius=6)

        # Label phím
        lbl = self.font.render(label, True, (140, 140, 140))
        self.screen.blit(lbl, lbl.get_rect(centerx=x + W // 2, y=y + 5))
        # Tên ability
        nm  = self.font.render(name[:7], True, color if ready else (90, 90, 90))
        self.screen.blit(nm, nm.get_rect(centerx=x + W // 2, y=y + 26))
        # Cooldown bar ở đáy
        bar_y = y + h - 8
        pygame.draw.rect(self.screen, (30, 30, 40), (x + 6, bar_y, W - 12, 5))
        if cooldown > 0:
            fill = int((W - 12) * (1.0 - min(timer / cooldown, 1.0)))
            if fill > 0:
                pygame.draw.rect(self.screen, color, (x + 6, bar_y, fill, 5))
        # Timer text khi đang hồi
        if not ready:
            t_surf = self.font.render(f"{timer:.1f}s", True, (180, 180, 180))
            self.screen.blit(t_surf, t_surf.get_rect(
                centerx=x + W // 2, y=y + h - 24))

    def _draw_stats(self, player, y: int) -> None:
        """Hiển thị stats cơ bản (armor, regen, xp_range) nếu > 0."""
        parts = []
        if player.armor > 0:
            parts.append((f"Armor {int(player.armor)}%", (120, 180, 255)))
        if player.hp_regen > 0:
            parts.append((f"Regen {player.hp_regen:.0f}/s", (80, 220, 120)))
        if player.xp_range > 0:
            parts.append((f"XP +{int(player.xp_range)}px", (255, 220, 80)))
        x = self.BAR_X
        for text, color in parts:
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (x, y))
            x += surf.get_width() + 14

    def _should_draw_overload(self, player) -> bool:
        return (
            getattr(player, 'lightning_overload', 0.0) > 0
            or self._active_spell_has_lightning(player)
        )

    def _active_spell_has_lightning(self, player) -> bool:
        from logic.rune.elements.lightning_rune import LightningRune

        spell = player.get_active_spell()
        return any(isinstance(rune, LightningRune) for rune in spell.rune_tree.elements)

    def _draw_overload_bar(self, player, y: int) -> None:
        ratio = max(0.0, min(getattr(player, 'lightning_overload', 0.0), 1.0))
        overloaded = getattr(player, 'lightning_overloaded', False)
        label = "OVERLOAD LOCKED" if overloaded else "OVERLOAD"
        fill_color = (255, 120, 50) if overloaded else (90, 220, 255)
        border_color = (255, 180, 90) if overloaded else (120, 240, 255)

        pygame.draw.rect(self.screen, (12, 24, 34),
                         (self.BAR_X, y, self.BAR_W, self.XP_H))
        fill_w = int(self.BAR_W * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, fill_color,
                             (self.BAR_X, y, fill_w, self.XP_H))
        pygame.draw.rect(self.screen, border_color,
                         (self.BAR_X, y, self.BAR_W, self.XP_H), 1)
        text = self.font.render(label, True, (245, 250, 255))
        self.screen.blit(text, (self.BAR_X + 4, y - 2))

    def _draw_spell_bar(self, player) -> None:
        """Thanh 3 chiêu ở dưới màn hình: Q ◄ [Chiêu 1] [Chiêu 2] [Chiêu 3] ► E"""
        BOX_W, BOX_H = 220, 60
        GAP          = 12
        BAR_Y        = SCREEN_H - BOX_H - 8
        total_w      = len(player.spells) * BOX_W + (len(player.spells) - 1) * GAP
        start_x      = (SCREEN_W - total_w) // 2

        # Gợi ý phím Q / E
        q_surf = self.font.render("Q ◄", True, (160, 160, 160))
        e_surf = self.font.render("► E", True, (160, 160, 160))
        self.screen.blit(q_surf, (start_x - q_surf.get_width() - 8,
                                  BAR_Y + BOX_H // 2 - q_surf.get_height() // 2))
        self.screen.blit(e_surf, (start_x + total_w + 8,
                                  BAR_Y + BOX_H // 2 - e_surf.get_height() // 2))

        # Ultimate + Dash cooldown (bên phải spell bar)
        ult_x = start_x + total_w + 24
        self._draw_cooldown_slot(
            ult_x, BAR_Y, BOX_H,
            label="RMB",
            name="ULTIMATE",
            timer=player.ultimate_timer,
            cooldown=player.ultimate_cooldown,
            color=(220, 80, 255),
        )
        dash_x = ult_x + 86
        ma = player.movement_ability
        self._draw_cooldown_slot(
            dash_x, BAR_Y, BOX_H,
            label="SPACE",
            name=ma.NAME,
            timer=ma.timer,
            cooldown=ma.COOLDOWN,
            color=ma.COLOR,
        )

        for i, spell in enumerate(player.spells):
            x      = start_x + i * (BOX_W + GAP)
            active = (i == player.active_spell_index)

            # Nền box
            bg_col = (40, 50, 70) if active else (20, 20, 30)
            bd_col = (255, 215, 0) if active else (70, 70, 90)
            bd_w   = 3 if active else 1
            box_surf = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
            box_surf.fill((*bg_col, 200))
            self.screen.blit(box_surf, (x, BAR_Y))
            pygame.draw.rect(self.screen, bd_col,
                             (x, BAR_Y, BOX_W, BOX_H), bd_w, border_radius=6)

            # Tên chiêu
            name_col  = (255, 215, 0) if active else (160, 160, 160)
            name_surf = self.font.render(spell.name, True, name_col)
            self.screen.blit(name_surf, (x + 8, BAR_Y + 6))

            # Mô tả combo ngắn
            desc      = spell.rune_tree.describe()
            desc_surf = self.font.render(desc[:28], True, (180, 200, 180))
            self.screen.blit(desc_surf, (x + 8, BAR_Y + 30))

            # Cooldown bar (nếu có fire_timer trên spell)
            ft = getattr(spell, 'fire_timer', 0.0)
            fr = getattr(spell, 'fire_rate', player.fire_rate)
            if ft > 0 and fr > 0:
                ratio   = min(ft / fr, 1.0)
                cd_w    = int((BOX_W - 16) * (1.0 - ratio))
                pygame.draw.rect(self.screen, (30, 30, 40),
                                 (x + 8, BAR_Y + BOX_H - 8, BOX_W - 16, 5))
                if cd_w > 0:
                    pygame.draw.rect(self.screen, (80, 200, 255),
                                     (x + 8, BAR_Y + BOX_H - 8, cd_w, 5))
