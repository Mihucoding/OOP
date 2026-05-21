import os
import math
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
    ADDITIVE_EFFECT_KINDS = {
        "lightning_hit",
        "lightning_beam",
        "lightning_ultimate",
        "lightning_overload",
    }

    def __init__(self, screen: pygame.Surface):
        self.screen       = screen
        self.sprite_cache: dict[str, pygame.Surface] = {}
        self.zoom = 1.60
        self.player_animations: dict[str, list[pygame.Surface]] = {}
        self.player_frame_size = 128
        self.player_draw_size = (112, 112)
        self.player_anim_ms = 90
        self.player_anim_state = None
        self.player_anim_started_ms = 0
        self.effect_animations: dict[str, list[pygame.Surface]] = {}
        self.effect_glow_animations: dict[str, list[pygame.Surface]] = {}
        self.world_map = None
        self._load_player_animations()
        self._load_effect_animations()
        try:
            from ui.tile_map import WorldMap
            self.world_map = WorldMap()
        except Exception:
            self.world_map = None

    # ── Tiện ích ──────────────────────────────────────────────────────────────

    def load_sprite(self, name: str, path: str, size: tuple) -> None:
        try:
            img = pygame.image.load(path).convert_alpha()
            self.sprite_cache[name] = pygame.transform.scale(img, size)
        except Exception:
            pass  # fallback vẽ shape nếu thiếu asset

    def _load_player_animations(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sprite_dir = os.path.join(
            root_dir, "assets", "sprites", "male_hero_free", "individual_sheets")
        sheets = {
            "idle": "male_hero-idle.png",
            "run": "male_hero-run.png",
            "dash": "male_hero-jump.png",
            "hurt": "male_hero-fall.png",
            "attack": "male_hero-combo_1.png",
        }
        for anim_name, filename in sheets.items():
            frames = self._slice_player_sheet(os.path.join(sprite_dir, filename))
            if frames:
                self.player_animations[anim_name] = frames

    def _slice_player_sheet(self, path: str) -> list[pygame.Surface]:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return []

        frame_count = sheet.get_width() // self.player_frame_size
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(
                i * self.player_frame_size,
                0,
                self.player_frame_size,
                self.player_frame_size,
            )
            frame = sheet.subsurface(rect).copy()
            frames.append(pygame.transform.scale(frame, self.player_draw_size))
        return frames

    def _load_effect_animations(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        effect_root = os.path.join(
            root_dir, "assets", "sprites",
            "Pixel Art Skill Animations - Lightning")
        configs = {
            "lightning_hit": {
                "folder": os.path.join(effect_root, "VFX1", "Frames"),
                "size": (160, 80),
            },
            "lightning_beam": {
                "folder": os.path.join(effect_root, "VFX1", "Frames"),
                "size": (256, 128),
            },
            "lightning_ultimate": {
                "folder": os.path.join(effect_root, "VFX3", "Frames"),
                "size": (140, 280),
            },
            "lightning_overload": {
                "folder": os.path.join(effect_root, "VFX6", "Frames"),
                "size": (150, 150),
            },
        }
        for kind, config in configs.items():
            frames = self._load_effect_frames(config["folder"], config["size"])
            if frames:
                self.effect_animations[kind] = frames
                if kind in self.ADDITIVE_EFFECT_KINDS:
                    self.effect_glow_animations[kind] = [
                        frame.premul_alpha() for frame in frames
                    ]

    def _load_effect_frames(self, folder: str, size: tuple[int, int]) -> list[pygame.Surface]:
        if not os.path.isdir(folder):
            return []

        frame_files = sorted(
            name for name in os.listdir(folder)
            if name.lower().endswith(".png"))
        frames = []
        for filename in frame_files:
            path = os.path.join(folder, filename)
            try:
                frame = pygame.image.load(path).convert_alpha()
            except Exception:
                continue
            frames.append(pygame.transform.scale(frame, size))
        return frames

    def _zoom_surface(self, image: pygame.Surface, smooth: bool = False) -> pygame.Surface:
        if self.zoom == 1.0:
            return image
        w = max(1, int(image.get_width() * self.zoom))
        h = max(1, int(image.get_height() * self.zoom))
        scaler = pygame.transform.smoothscale if smooth else pygame.transform.scale
        return scaler(image, (w, h))

    def _zoom_len(self, value: float) -> int:
        return max(1, int(value * self.zoom))

    def world_to_screen(self, wx, wy, cam_x, cam_y) -> tuple:
        sx = (wx - cam_x) * self.zoom + SCREEN_W / 2
        sy = (wy - cam_y) * self.zoom + SCREEN_H / 2
        return (int(sx), int(sy))

    # ── Nền ───────────────────────────────────────────────────────────────────

    def draw_background(self, cam_x: float, cam_y: float) -> None:
        if self.world_map:
            self.screen.fill((0, 0, 0))
            self.world_map.draw(self.screen, cam_x, cam_y, SCREEN_W, SCREEN_H, self.zoom)
            return

        self.screen.fill(self.COLOR_BG)
        # Grid động: dịch chuyển theo camera để thấy player đang di chuyển
        grid_size = max(1, int(GRID_SIZE * self.zoom))
        offset_x = int((-cam_x * self.zoom) % grid_size)
        offset_y = int((-cam_y * self.zoom) % grid_size)
        for gx in range(offset_x, SCREEN_W + grid_size, grid_size):
            pygame.draw.line(self.screen, self.COLOR_GRID, (gx, 0), (gx, SCREEN_H))
        for gy in range(offset_y, SCREEN_H + grid_size, grid_size):
            pygame.draw.line(self.screen, self.COLOR_GRID, (0, gy), (SCREEN_W, gy))

    # ── Entities ──────────────────────────────────────────────────────────────

    def draw_player(self, player, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(player.x, player.y, cam_x, cam_y)
        anim_name = self._get_player_anim_name(player)
        frames = self.player_animations.get(anim_name)
        if frames:
            frame_idx = self._get_player_frame_idx(anim_name, len(frames), player)
            img = self._zoom_surface(frames[frame_idx])
            if getattr(player, "facing_dir", 1) < 0:
                img = pygame.transform.flip(img, True, False)
            self.screen.blit(img, img.get_rect(center=(sx, sy + self._get_player_bob(anim_name))))
        elif 'player' in self.sprite_cache:
            img = self._zoom_surface(self.sprite_cache['player'])
            self.screen.blit(img, img.get_rect(center=(sx, sy)))
        else:
            radius = self._zoom_len(player.radius)
            pygame.draw.circle(self.screen, self.COLOR_PLAYER, (sx, sy), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 2)

    def _get_player_anim_name(self, player) -> str:
        if getattr(player, "hurt_timer", 0.0) > 0:
            return "hurt"
        if getattr(player, "dash_timer", 0.0) > 0:
            return "dash"
        if getattr(player, "attack_timer", 0.0) > 0:
            return "attack"
        return "run" if getattr(player, "is_moving", False) else "idle"

    def _get_player_frame_idx(self, anim_name: str, frame_count: int, player) -> int:
        now = pygame.time.get_ticks()
        if anim_name != self.player_anim_state:
            self.player_anim_state = anim_name
            self.player_anim_started_ms = now

        elapsed = max(0, now - self.player_anim_started_ms)
        frame_ms = self._get_player_frame_ms(anim_name, player)
        return (elapsed // frame_ms) % frame_count

    def _get_player_frame_ms(self, anim_name: str, player) -> int:
        if anim_name == "run":
            speed_ratio = getattr(player, "move_speed_ratio", 1.0)
            return max(55, int(95 - 30 * speed_ratio))
        if anim_name == "attack":
            return 48
        if anim_name == "dash":
            return 55
        if anim_name == "hurt":
            return 80
        return 120

    def _get_player_bob(self, anim_name: str) -> int:
        if anim_name != "run":
            return 0
        elapsed = max(0, pygame.time.get_ticks() - self.player_anim_started_ms)
        return int(math.sin(elapsed / 85.0) * self.zoom)

    def draw_enemy(self, enemy, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(enemy.x, enemy.y, cam_x, cam_y)

        # Status halo (vòng màu bên ngoài)
        self._draw_status_halo(enemy, sx, sy)

        # Thân
        from logic.entities.ranged_enemy import RangedEnemy
        color = self.COLOR_RANGED if isinstance(enemy, RangedEnemy) else self.COLOR_ENEMY
        radius = self._zoom_len(enemy.radius)
        pygame.draw.circle(self.screen, color, (sx, sy), radius)

        # HP bar
        self._draw_hp_bar(enemy, sx, sy, radius)

    def draw_boss(self, boss, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(boss.x, boss.y, cam_x, cam_y)

        # AoE vòng cảnh báo
        if boss.aoe_active:
            aoe_r   = self._zoom_len(boss.AOE_RADIUS)
            aoe_surf = pygame.Surface((aoe_r * 2, aoe_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aoe_surf, (255, 50, 50, 55),
                               (aoe_r, aoe_r), aoe_r)
            self.screen.blit(aoe_surf, (sx - aoe_r, sy - aoe_r))
            pygame.draw.circle(self.screen, (255, 80, 80), (sx, sy), aoe_r, 2)

        self._draw_status_halo(boss, sx, sy)

        # Thân boss
        body_color = (255, 120, 0) if boss.is_charging else self.COLOR_BOSS
        radius = self._zoom_len(boss.radius)
        pygame.draw.circle(self.screen, body_color, (sx, sy), radius)
        pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 3)

        # HP bar (to hơn)
        self._draw_hp_bar(boss, sx, sy, radius, bar_h=8, color=(200, 0, 220))

    def draw_bullet(self, bullet, cam_x, cam_y) -> None:
        sx, sy  = self.world_to_screen(bullet.x, bullet.y, cam_x, cam_y)
        is_crit = getattr(bullet, 'is_crit', False)
        color   = (255, 60, 60) if is_crit else self.COLOR_BULLET
        radius  = self._zoom_len(bullet.radius + (3 if is_crit else 0))
        pygame.draw.circle(self.screen, color, (sx, sy), radius)
        if is_crit:
            pygame.draw.circle(self.screen, (255, 200, 50), (sx, sy), radius, 2)

    def draw_enemy_bullet(self, eb, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(eb.x, eb.y, cam_x, cam_y)
        pygame.draw.circle(self.screen, self.COLOR_ENEMY_BULLET, (sx, sy), self._zoom_len(eb.radius))

    def draw_xp_orb(self, orb, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(orb.x, orb.y, cam_x, cam_y)
        pygame.draw.circle(self.screen, self.COLOR_XP_ORB, (sx, sy), self._zoom_len(orb.radius))

    def draw_effects(self, effects: list[dict], cam_x, cam_y) -> None:
        for effect in effects:
            frames = self.effect_animations.get(effect.get('kind'))
            if not frames:
                continue
            glow_frames = self.effect_glow_animations.get(effect.get('kind'))

            duration = max(effect.get('duration', 0.1), 0.001)
            age = effect.get('age', 0.0)
            if effect.get('loop_anim'):
                frame_ms = max(1, int(effect.get('frame_ms', self.player_anim_ms)))
                frame_idx = (pygame.time.get_ticks() // frame_ms) % len(frames)
            else:
                frame_idx = min(int((age / duration) * len(frames)), len(frames) - 1)
            if effect.get('kind') == 'lightning_beam':
                glow_frame = None if glow_frames is None else glow_frames[frame_idx]
                self._draw_beam_effect(effect, frames[frame_idx], glow_frame, cam_x, cam_y)
                continue

            img = self._zoom_surface(frames[frame_idx])
            sx, sy = self.world_to_screen(effect['x'], effect['y'], cam_x, cam_y)
            if effect.get('kind') == 'lightning_ultimate':
                rect = img.get_rect(midbottom=(sx, sy + self._zoom_len(36)))
            else:
                rect = img.get_rect(center=(sx, sy))
            self.screen.blit(img, rect)
            if glow_frames is not None:
                glow = self._zoom_surface(glow_frames[frame_idx])
                self.screen.blit(glow, rect, special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_beam_effect(
        self,
        effect: dict,
        frame: pygame.Surface,
        glow_frame: pygame.Surface | None,
        cam_x,
        cam_y,
    ) -> None:
        sx, sy = self.world_to_screen(effect['x'], effect['y'], cam_x, cam_y)
        ex, ey = self.world_to_screen(effect['x2'], effect['y2'], cam_x, cam_y)
        dx = ex - sx
        dy = ey - sy
        if effect.get('fixed_size'):
            beam = self._zoom_surface(frame)
            glow = None if glow_frame is None else self._zoom_surface(glow_frame)
        else:
            length = max(1, int(math.hypot(dx, dy)))
            height = self._zoom_len(54)
            beam = pygame.transform.scale(frame, (length, height))
            glow = None if glow_frame is None else pygame.transform.scale(glow_frame, (length, height))
        angle = -math.degrees(math.atan2(dy, dx))
        beam = pygame.transform.rotate(beam, angle)
        rect = beam.get_rect(center=((sx + ex) // 2, (sy + ey) // 2))
        self.screen.blit(beam, rect)
        if glow is not None:
            glow = pygame.transform.rotate(glow, angle)
            self.screen.blit(glow, glow.get_rect(center=rect.center), special_flags=pygame.BLEND_RGBA_ADD)

    # ── Render tổng ───────────────────────────────────────────────────────────

    def draw_all(self, player, enemies, boss, bullets, xp_orbs,
                 enemy_bullets, cam_x, cam_y,
                 effects=None,
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
        if effects:
            self.draw_effects(effects, cam_x, cam_y)
        self.draw_player(player, cam_x, cam_y)

    def _draw_ultimate_flash(self, info: dict, cam_x, cam_y) -> None:
        """Vẽ vòng sáng AoE khi ultimate kích hoạt."""
        sx, sy   = self.world_to_screen(info['cx'], info['cy'], cam_x, cam_y)
        radius   = self._zoom_len(info['radius'])
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
                    (sx, sy), self._zoom_len(entity.radius + 4), 3)
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
