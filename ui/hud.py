import os
import pygame

SCREEN_W, SCREEN_H = 1280, 720


class HUD:
    """Vẽ giao diện: HP bar, XP bar, level, wave, rune tree hiện tại."""

    BAR_X = 14
    BAR_Y = 12
    BAR_W = 300
    HP_H  = 24
    XP_H  = 12

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font   = font
        self.ui_assets = {}
        self._load_ui_assets()

    def _load_ui_assets(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_dir = os.path.join(
            root_dir, "assets", "map", "Tiny Swords (Free Pack)",
            "UI Elements", "UI Elements")
        paths = {
            "bar_big_base": os.path.join(ui_dir, "Bars", "BigBar_Base.png"),
            "bar_big_fill": os.path.join(ui_dir, "Bars", "BigBar_Fill.png"),
            "bar_small_base": os.path.join(ui_dir, "Bars", "SmallBar_Base.png"),
            "bar_small_fill": os.path.join(ui_dir, "Bars", "SmallBar_Fill.png"),
            "button_big_blue": os.path.join(ui_dir, "Buttons", "BigBlueButton_Regular.png"),
            "button_big_red": os.path.join(ui_dir, "Buttons", "BigRedButton_Regular.png"),
            "button_small_blue": os.path.join(ui_dir, "Buttons", "SmallBlueSquareButton_Regular.png"),
            "button_small_blue_pressed": os.path.join(ui_dir, "Buttons", "SmallBlueSquareButton_Pressed.png"),
            "button_small_red": os.path.join(ui_dir, "Buttons", "SmallRedSquareButton_Regular.png"),
            "button_small_red_pressed": os.path.join(ui_dir, "Buttons", "SmallRedSquareButton_Pressed.png"),
        }
        for name, path in paths.items():
            try:
                self.ui_assets[name] = pygame.image.load(path).convert_alpha()
            except Exception:
                pass

    def _scaled_asset(self, name: str, size: tuple[int, int]) -> pygame.Surface | None:
        asset = self.ui_assets.get(name)
        if asset is None:
            return None
        return pygame.transform.scale(asset, size)

    def _tinted_asset(self, name: str, size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface | None:
        asset = self._scaled_asset(name, size)
        if asset is None:
            return None
        tinted = asset.copy()
        tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def _draw_asset_bar(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        ratio: float,
        fill_color: tuple[int, int, int],
        text: str | None = None,
        text_color: tuple[int, int, int] = (255, 255, 255),
        small: bool = False,
    ) -> None:
        ratio = max(0.0, min(1.0, ratio))
        rect = pygame.Rect(x, y, w, h)
        inset = 3 if small else 4
        inner = rect.inflate(-inset * 2, -inset * 2)

        pygame.draw.rect(self.screen, (5, 8, 12), rect.move(2, 2), border_radius=3)
        pygame.draw.rect(self.screen, (31, 34, 43), rect, border_radius=3)
        pygame.draw.rect(self.screen, (218, 198, 122), rect, 2, border_radius=3)
        pygame.draw.rect(self.screen, (13, 17, 24), inner, border_radius=2)

        fill_w = int(inner.width * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(inner.x, inner.y, fill_w, inner.height)
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=2)
            highlight_h = max(1, inner.height // 4)
            highlight = tuple(min(255, c + 45) for c in fill_color)
            pygame.draw.rect(
                self.screen,
                highlight,
                (fill_rect.x, fill_rect.y, fill_rect.width, highlight_h),
                border_radius=2,
            )

        if text:
            surf = self.font.render(text, True, text_color)
            self.screen.blit(surf, surf.get_rect(center=(x + w // 2, y + h // 2 - 1)))

    def _draw_button_asset(self, rect: pygame.Rect, color: str = "blue", pressed: bool = False) -> None:
        if rect.width > 110:
            key = "button_big_blue" if color == "blue" else "button_big_red"
        else:
            if color == "red":
                key = "button_small_red_pressed" if pressed else "button_small_red"
            else:
                key = "button_small_blue_pressed" if pressed else "button_small_blue"
        button = self._scaled_asset(key, (rect.width, rect.height))
        if button is not None:
            self.screen.blit(button, rect)
        else:
            bg = (36, 58, 86) if color == "blue" else (74, 32, 34)
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, (210, 220, 230), rect, 1, border_radius=6)

    def draw(self, player, wave_info: str) -> None:
        # ── HP bar ────────────────────────────────────────────────────────────
        bar_x, bar_y = self.BAR_X, self.BAR_Y
        self._draw_asset_bar(
            bar_x,
            bar_y,
            self.BAR_W,
            self.HP_H,
            player.get_hp_ratio(),
            (255, 58, 58),
            text=f"HP  {int(player.hp)} / {int(player.max_hp)}",
        )

        # ── XP bar ────────────────────────────────────────────────────────────
        xp_y = bar_y + self.HP_H + 4
        self._draw_asset_bar(
            bar_x,
            xp_y,
            self.BAR_W,
            self.XP_H,
            player.get_xp_ratio(),
            (70, 235, 100),
            small=True,
        )

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

    def _draw_panel(self, rect: pygame.Rect, border: tuple[int, int, int],
                    bg: tuple[int, int, int], active: bool = False) -> None:
        pygame.draw.rect(self.screen, (4, 6, 10), rect.move(3, 3), border_radius=5)
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=5)
        if active:
            pygame.draw.rect(self.screen, (255, 240, 150), rect.inflate(-8, -8), 1, border_radius=4)

    def _render_fit(self, text: str, color: tuple[int, int, int],
                    max_w: int) -> pygame.Surface:
        surf = self.font.render(text, True, color)
        if surf.get_width() <= max_w:
            return surf
        clipped = text
        while clipped and self.font.size(clipped + "...")[0] > max_w:
            clipped = clipped[:-1]
        return self.font.render(clipped.rstrip() + "...", True, color)

    def _draw_cooldown_slot(self, x: int, y: int, h: int,
                            label: str, name: str,
                            timer: float, cooldown: float,
                            color: tuple) -> None:
        """Ô cooldown nhỏ: tên + thanh hồi chiêu."""
        W = 82
        ready = timer <= 0.0
        rect = pygame.Rect(x, y, W, h)
        border = color if ready else (95, 104, 116)
        bg = (24, 40, 50) if ready else (27, 29, 34)
        self._draw_panel(rect, border, bg, active=ready)

        # Label phím
        lbl = self._render_fit(label, (175, 184, 194), W - 14)
        self.screen.blit(lbl, lbl.get_rect(centerx=rect.centerx, y=y + 7))
        # Tên ability
        name_col = color if ready else (120, 124, 132)
        nm = self._render_fit(name.title(), name_col, W - 14)
        self.screen.blit(nm, nm.get_rect(centerx=rect.centerx, y=y + 27))
        # Cooldown bar ở đáy
        bar_rect = pygame.Rect(x + 10, y + h - 11, W - 20, 5)
        pygame.draw.rect(self.screen, (12, 16, 22), bar_rect, border_radius=2)
        if cooldown > 0:
            fill = int(bar_rect.width * (1.0 - min(timer / cooldown, 1.0)))
            if fill > 0:
                pygame.draw.rect(
                    self.screen,
                    color,
                    (bar_rect.x, bar_rect.y, fill, bar_rect.height),
                    border_radius=2,
                )
        # Timer text khi đang hồi
        if not ready:
            t_surf = self.font.render(f"{timer:.1f}s", True, (215, 220, 228))
            self.screen.blit(t_surf, t_surf.get_rect(centerx=rect.centerx, y=y + 43))

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
        self._draw_asset_bar(
            self.BAR_X,
            y,
            self.BAR_W,
            self.XP_H,
            ratio,
            fill_color,
            text=label,
            text_color=(245, 250, 255),
            small=True,
        )

    def _draw_spell_bar(self, player) -> None:
        """Thanh 3 chiêu ở dưới màn hình: Q ◄ [Chiêu 1] [Chiêu 2] [Chiêu 3] ► E"""
        BOX_W, BOX_H = 210, 62
        GAP          = 10
        BAR_Y        = SCREEN_H - BOX_H - 14
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
        ult_x = start_x + total_w + 40
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
            rect = pygame.Rect(x, BAR_Y, BOX_W, BOX_H)
            border = (255, 225, 95) if active else (98, 112, 128)
            bg = (24, 45, 57) if active else (28, 31, 38)
            self._draw_panel(rect, border, bg, active=active)
            pygame.draw.rect(self.screen, border, (x + 8, BAR_Y + 8, 4, BOX_H - 16), border_radius=2)

            # Tên chiêu
            name_col  = (255, 215, 0) if active else (160, 160, 160)
            name_surf = self._render_fit(spell.name, name_col, BOX_W - 28)
            self.screen.blit(name_surf, (x + 18, BAR_Y + 6))

            # Mô tả combo ngắn
            desc      = spell.rune_tree.describe()
            desc_col = (190, 220, 205) if active else (138, 148, 152)
            desc_surf = self._render_fit(desc, desc_col, BOX_W - 28)
            self.screen.blit(desc_surf, (x + 18, BAR_Y + 30))

            # Cooldown bar (nếu có fire_timer trên spell)
            ft = getattr(spell, 'fire_timer', 0.0)
            fr = getattr(spell, 'fire_rate', player.fire_rate)
            bar_rect = pygame.Rect(x + 18, BAR_Y + BOX_H - 12, BOX_W - 36, 5)
            pygame.draw.rect(self.screen, (12, 16, 22), bar_rect, border_radius=2)
            if ft > 0 and fr > 0:
                ratio   = min(ft / fr, 1.0)
                cd_w    = int(bar_rect.width * (1.0 - ratio))
                if cd_w > 0:
                    pygame.draw.rect(
                        self.screen,
                        (80, 200, 255),
                        (bar_rect.x, bar_rect.y, cd_w, bar_rect.height),
                        border_radius=2,
                    )
            else:
                pygame.draw.rect(self.screen, border, bar_rect, border_radius=2)
