import pygame

SCREEN_W, SCREEN_H = 1280, 720
GRID_SIZE = 64


class Renderer:
    """
    Vẽ toàn bộ game world.
    Camera: camera_x/y là world position của player → player luôn ở center màn hình.
    """

    COLOR_BG          = (30, 30, 30)
    COLOR_GRID        = (45, 45, 45)
    COLOR_PLAYER      = (80, 180, 255)
    COLOR_ENEMY       = (220, 60, 60)
    COLOR_RANGED      = (0, 210, 210)
    COLOR_BOSS        = (180, 0, 200)
    COLOR_BULLET      = (255, 255, 100)
    COLOR_ENEMY_BULLET = (255, 120, 0)
    COLOR_XP_ORB      = (100, 255, 150)

    # Màu status halo
    COLOR_BURN   = (255, 120, 0)
    COLOR_CHILL  = (150, 200, 255)
    COLOR_SLOW   = (100, 180, 255)
    COLOR_STUN   = (255, 230, 50)
    COLOR_POISON = (120, 255, 80)

    def __init__(self, screen: pygame.Surface):
        self.screen       = screen
        self.sprite_cache: dict[str, pygame.Surface] = {}

    # ── Tiện ích ──────────────────────────────────────────────────────────────

    def load_sprite(self, name: str, path: str, size: tuple) -> None:
        try:
            img = pygame.image.load(path).convert_alpha()
            self.sprite_cache[name] = pygame.transform.scale(img, size)
        except Exception:
            pass  # fallback vẽ shape nếu thiếu asset

    def world_to_screen(self, wx, wy, cam_x, cam_y) -> tuple:
        sx = wx - cam_x + SCREEN_W / 2
        sy = wy - cam_y + SCREEN_H / 2
        return (int(sx), int(sy))

    # ── Nền ───────────────────────────────────────────────────────────────────

    def draw_background(self, cam_x: float, cam_y: float) -> None:
        self.screen.fill(self.COLOR_BG)
        # Grid động: dịch chuyển theo camera để thấy player đang di chuyển
        offset_x = int(-cam_x % GRID_SIZE)
        offset_y = int(-cam_y % GRID_SIZE)
        for gx in range(offset_x, SCREEN_W + GRID_SIZE, GRID_SIZE):
            pygame.draw.line(self.screen, self.COLOR_GRID, (gx, 0), (gx, SCREEN_H))
        for gy in range(offset_y, SCREEN_H + GRID_SIZE, GRID_SIZE):
            pygame.draw.line(self.screen, self.COLOR_GRID, (0, gy), (SCREEN_W, gy))

    # ── Entities ──────────────────────────────────────────────────────────────

    def draw_player(self, player, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(player.x, player.y, cam_x, cam_y)
        if 'player' in self.sprite_cache:
            img = self.sprite_cache['player']
            self.screen.blit(img, img.get_rect(center=(sx, sy)))
        else:
            pygame.draw.circle(self.screen, self.COLOR_PLAYER, (sx, sy), player.radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), player.radius, 2)

    def draw_enemy(self, enemy, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(enemy.x, enemy.y, cam_x, cam_y)

        # Status halo (vòng màu bên ngoài)
        self._draw_status_halo(enemy, sx, sy)

        # Thân
        from logic.entities.ranged_enemy import RangedEnemy
        color = self.COLOR_RANGED if isinstance(enemy, RangedEnemy) else self.COLOR_ENEMY
        pygame.draw.circle(self.screen, color, (sx, sy), enemy.radius)

        # HP bar
        self._draw_hp_bar(enemy, sx, sy, enemy.radius)

    def draw_boss(self, boss, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(boss.x, boss.y, cam_x, cam_y)

        # AoE vòng cảnh báo
        if boss.aoe_active:
            aoe_r   = boss.AOE_RADIUS
            aoe_surf = pygame.Surface((aoe_r * 2, aoe_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aoe_surf, (255, 50, 50, 55),
                               (aoe_r, aoe_r), aoe_r)
            self.screen.blit(aoe_surf, (sx - aoe_r, sy - aoe_r))
            pygame.draw.circle(self.screen, (255, 80, 80), (sx, sy), aoe_r, 2)

        self._draw_status_halo(boss, sx, sy)

        # Thân boss
        body_color = (255, 120, 0) if boss.is_charging else self.COLOR_BOSS
        pygame.draw.circle(self.screen, body_color, (sx, sy), boss.radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), boss.radius, 3)

        # HP bar (to hơn)
        self._draw_hp_bar(boss, sx, sy, boss.radius, bar_h=8, color=(200, 0, 220))

    def draw_bullet(self, bullet, cam_x, cam_y) -> None:
        sx, sy  = self.world_to_screen(bullet.x, bullet.y, cam_x, cam_y)
        is_crit = getattr(bullet, 'is_crit', False)
        color   = (255, 60, 60) if is_crit else self.COLOR_BULLET
        radius  = bullet.radius + (3 if is_crit else 0)
        pygame.draw.circle(self.screen, color, (sx, sy), radius)
        if is_crit:
            pygame.draw.circle(self.screen, (255, 200, 50), (sx, sy), radius, 2)

    def draw_enemy_bullet(self, eb, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(eb.x, eb.y, cam_x, cam_y)
        pygame.draw.circle(self.screen, self.COLOR_ENEMY_BULLET, (sx, sy), eb.radius)

    def draw_xp_orb(self, orb, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(orb.x, orb.y, cam_x, cam_y)
        pygame.draw.circle(self.screen, self.COLOR_XP_ORB, (sx, sy), orb.radius)

    # ── Render tổng ───────────────────────────────────────────────────────────

    def draw_all(self, player, enemies, boss, bullets, xp_orbs,
                 enemy_bullets, cam_x, cam_y,
                 ultimate_flash=None) -> None:
        self.draw_background(cam_x, cam_y)
        # Ultimate AoE flash (dưới các entity)
        if ultimate_flash:
            self._draw_ultimate_flash(ultimate_flash, cam_x, cam_y)
        for orb in xp_orbs:
            if orb.alive:
                self.draw_xp_orb(orb, cam_x, cam_y)
        for enemy in enemies:
            if enemy.alive:
                self.draw_enemy(enemy, cam_x, cam_y)
        if boss and boss.alive:
            self.draw_boss(boss, cam_x, cam_y)
        for eb in enemy_bullets:
            if eb.alive:
                self.draw_enemy_bullet(eb, cam_x, cam_y)
        for bullet in bullets:
            if bullet.alive:
                self.draw_bullet(bullet, cam_x, cam_y)
        self.draw_player(player, cam_x, cam_y)

    def _draw_ultimate_flash(self, info: dict, cam_x, cam_y) -> None:
        """Vẽ vòng sáng AoE khi ultimate kích hoạt."""
        sx, sy   = self.world_to_screen(info['cx'], info['cy'], cam_x, cam_y)
        radius   = int(info['radius'])
        r, g, b  = info['color']
        # Fade out theo duration còn lại
        alpha    = min(180, int(info['duration'] * 360))
        surf     = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (r, g, b, alpha),
                           (radius + 2, radius + 2), radius)
        pygame.draw.circle(surf, (r, g, b, min(255, alpha + 60)),
                           (radius + 2, radius + 2), radius, 4)
        self.screen.blit(surf, (sx - radius - 2, sy - radius - 2))

    # ── Helpers nội bộ ────────────────────────────────────────────────────────

    def _draw_status_halo(self, entity, sx: int, sy: int) -> None:
        """Vẽ vòng màu ngoài entity tuỳ theo status effect đang hoạt động."""
        _COLOR_MAP = {
            'burn':   self.COLOR_BURN,
            'chill':  self.COLOR_CHILL,
            'slow':   self.COLOR_SLOW,
            'stun':   self.COLOR_STUN,
            'poison': self.COLOR_POISON,
        }
        for eff in entity.status_effects:
            color = _COLOR_MAP.get(eff.type)
            if color:
                pygame.draw.circle(
                    self.screen, color,
                    (sx, sy), entity.radius + 4, 3)
                break  # Chỉ vẽ halo của effect đầu tiên

    def _draw_hp_bar(self, entity, sx: int, sy: int,
                     radius: int, bar_h: int = 4,
                     color=(220, 40, 40)) -> None:
        bar_w  = radius * 2
        bar_x  = sx - radius
        bar_y  = sy - radius - bar_h - 4
        # Nền đỏ tối
        pygame.draw.rect(self.screen, (60, 0, 0),
                         (bar_x, bar_y, bar_w, bar_h))
        fill_w = int(bar_w * entity.get_hp_ratio())
        if fill_w > 0:
            pygame.draw.rect(self.screen, color,
                             (bar_x, bar_y, fill_w, bar_h))
