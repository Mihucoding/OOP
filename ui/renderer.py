import os
import math
import pygame

from ui.vfx_manager import AnimatorPool, VFX_DISPLAY_SIZE

SCREEN_W, SCREEN_H = 640, 360
WINDOW_W, WINDOW_H = 1280, 720
PIXEL_SCALE = WINDOW_W // SCREEN_W
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
        self._bullet_pool = AnimatorPool()
        self._effect_pool = AnimatorPool()
        self.zoom = 1.0
        self.player_animations: dict[str, list[pygame.Surface]] = {}
        self.player_frame_size = 128
        self.player_draw_size = (48, 48)
        self.player_anim_ms = 90
        self.player_anim_state = None
        self.player_anim_started_ms = 0
        self.effect_animations: dict[str, list[pygame.Surface]] = {}
        self.effect_glow_animations: dict[str, list[pygame.Surface]] = {}
        self.mushroom_animations: dict[str, list[pygame.Surface]] = {}
        self.ranged_animations: dict[str, list[pygame.Surface]] = {}
        self.fast_animations: dict[str, list[pygame.Surface]] = {}
        self.tank_animations: dict[str, list[pygame.Surface]] = {}
        self.boss_animations: dict[str, list[pygame.Surface]] = {}
        self.world_map = None
        self.minimap_surface = None
        self.minimap_source_id = None
        self._load_player_animations()
        self._load_effect_animations()
        self._load_enemy_animations()
        self.wind_projectile_frames: list[pygame.Surface] = []
        self._load_wind_sprites()
        try:
            from ui.tiled_map import DEFAULT_MAP_FILE, TiledMap
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            custom_map_path = os.path.join(root_dir, DEFAULT_MAP_FILE)
            if os.path.exists(custom_map_path):
                self.world_map = TiledMap(custom_map_path)
            else:
                from ui.tile_map import WorldMap
                self.world_map = WorldMap()
        except Exception:
            try:
                from ui.tile_map import WorldMap
                self.world_map = WorldMap()
            except Exception:
                self.world_map = None
        self.last_leave_tick = pygame.time.get_ticks()
        self.leaves = []
        self.scaled_cache = {}  # Cache cho scaled images (xp orb, leaves...)

        # Load Gold Resource Highlight để thay thế cho XP Orb
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gold_highlight_path = os.path.join(
            root_dir,
            "assets",
            "map",
            "Tiny Swords (Free Pack)",
            "Terrain",
            "Resources",
            "Gold",
            "Gold Resource",
            "Gold_Resource_Highlight.png",
        )
        self.gold_orb_frames = []
        if os.path.exists(gold_highlight_path):
            try:
                sheet = pygame.image.load(gold_highlight_path).convert_alpha()
                frame_w = 128
                frame_h = 128
                for x in range(0, sheet.get_width() - frame_w + 1, frame_w):
                    frame = sheet.subsurface((x, 0, frame_w, frame_h)).copy()
                    self.gold_orb_frames.append(frame)
            except Exception:
                pass

        # Load Sheep animations
        sheep_dir = os.path.join(
            root_dir,
            "assets",
            "map",
            "Tiny Swords (Free Pack)",
            "Terrain",
            "Resources",
            "Meat",
            "Sheep",
        )
        self.sheep_animations = {}
        sheep_configs = {
            "idle": ("Sheep_Idle.png", 6),
            "wander": ("Sheep_Move.png", 4),
            "eating": ("Sheep_Grass.png", 12),
        }
        for state_name, (filename, frame_count) in sheep_configs.items():
            path = os.path.join(sheep_dir, filename)
            if os.path.exists(path):
                try:
                    sheet = pygame.image.load(path).convert_alpha()
                    frames = []
                    frame_w = 128
                    frame_h = 128
                    for i in range(frame_count):
                        frame = sheet.subsurface((i * frame_w, 0, frame_w, frame_h)).copy()
                        # Lưu trữ frame gốc 128x128, KHÔNG scale trước
                        frames.append(frame)
                    self.sheep_animations[state_name] = frames
                except Exception:
                    pass

        # Load Meat sprite
        meat_path = os.path.join(
            root_dir,
            "assets",
            "map",
            "Tiny Swords (Free Pack)",
            "Terrain",
            "Resources",
            "Meat",
            "Meat Resource",
            "Meat Resource.png",
        )
        self.meat_sprite = None
        if os.path.exists(meat_path):
            try:
                # Lưu trữ sprite gốc 64x64, KHÔNG scale trước
                self.meat_sprite = pygame.image.load(meat_path).convert_alpha()
            except Exception:
                pass

    def _load_wind_sprites(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wind_dir = os.path.join(root_dir, "assets", "sprites", "Wind Effect 01")
        proj_path = os.path.join(wind_dir, "Wind Projectile.png")
        self.wind_projectile_frames = self._slice_wind_sheet(proj_path)
        hit_path = os.path.join(wind_dir, "Wind Hit Effect.png")
        hit_frames = self._slice_wind_sheet(hit_path, display_size=(72, 72))
        if hit_frames:
            self.effect_animations['wind_hit'] = hit_frames

    def _slice_wind_sheet(self, path: str, display_size: tuple | None = None) -> list[pygame.Surface]:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return []
        w, h = sheet.get_width(), sheet.get_height()
        for frame_size in (32, 48, 64, 96, 128):
            if h % frame_size == 0 and w % frame_size == 0:
                cols = w // frame_size
                rows = h // frame_size
                frames = []
                for row in range(rows):
                    for col in range(cols):
                        rect = pygame.Rect(col * frame_size, row * frame_size, frame_size, frame_size)
                        frame = sheet.subsurface(rect).copy()
                        if display_size:
                            frame = pygame.transform.scale(frame, display_size)
                        frames.append(frame)
                return frames
        return [sheet]

    def _load_enemy_animations(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sprite_dir = os.path.join(root_dir, "assets", "sprites", "Mushroom")
        sheets = {
            "idle": "Mushroom-Idle.png",
            "run": "Mushroom-Run.png",
            "attack": "Mushroom-Attack.png",
            "hit": "Mushroom-Hit.png",
            "die": "Mushroom-Die.png",
        }
        for anim_name, filename in sheets.items():
            path = os.path.join(sprite_dir, filename)
            frames = self._slice_mushroom_sheet(path)
            if frames:
                self.mushroom_animations[anim_name] = frames

        # Load Ranged Enemy (Enemy3)
        ranged_dir = os.path.join(root_dir, "assets", "sprites", "Ranged")
        r_sheets = {
            "idle": "Enemy3-Idle.png",
            "run": "Enemy3-Fly.png",
            "hit": "Enemy3-Hit.png",
            "die": "Enemy3-Die.png",
        }
        for anim_name, filename in r_sheets.items():
            path = os.path.join(ranged_dir, filename)
            frames = self._slice_ranged_sheet(path)
            if frames:
                self.ranged_animations[anim_name] = frames

        # Load Fast Enemy (Bat)
        fast_dir = os.path.join(root_dir, "assets", "sprites", "Fast")
        f_sheets = {
            "idle": "Bat-IdleFly.png",
            "run": "Bat-Run.png",
            "hit": "Bat-Hurt.png",
            "die": "Bat-Die.png",
            "attack1": "Bat-Attack1.png",
            "attack2": "Bat-Attack2.png",
        }
        for anim_name, filename in f_sheets.items():
            path = os.path.join(fast_dir, filename)
            frames = self._slice_ranged_sheet(path)
            if frames:
                self.fast_animations[anim_name] = frames

        # Load Tank Enemy (Golem - Tank)
        tank_dir = os.path.join(root_dir, "assets", "sprites", "Tank")
        golem_sheets = {
            "idle": "Golem_1_idle.png",
            "run": "Golem_1_walk.png",
            "attack": "Golem_1_attack.png",
            "hit": "Golem_1_hurt.png",
            "die": "Golem_1_die.png",
        }
        for anim_name, filename in golem_sheets.items():
            path = os.path.join(tank_dir, filename)
            frames = self._slice_golem_sheet(path, scale=1.0)
            if frames:
                self.tank_animations[anim_name] = frames

        # Load Boss (Golem - Boss)
        boss_dir = os.path.join(root_dir, "assets", "sprites", "Boss")
        for anim_name, filename in golem_sheets.items():
            path = os.path.join(boss_dir, filename)
            frames = self._slice_golem_sheet(path, scale=2.5)
            if frames:
                self.boss_animations[anim_name] = frames

    def _slice_golem_sheet(self, path: str, scale: float) -> list[pygame.Surface]:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return []
        frame_w, frame_h = 90, 64
        frame_count = sheet.get_width() // frame_w
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
            frames.append(frame)
        return frames

    def _slice_ranged_sheet(self, path: str) -> list[pygame.Surface]:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return []
        frame_w, frame_h = 64, 64
        frame_count = sheet.get_width() // frame_w
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (frame_w, frame_h))
            frames.append(frame)
        return frames

    def _slice_mushroom_sheet(self, path: str) -> list[pygame.Surface]:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return []
        frame_w, frame_h = 80, 64
        frame_count = sheet.get_width() // frame_w
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (frame_w, frame_h))
            frames.append(frame)
        return frames

    # ── Tiện ích ──────────────────────────────────────────────────────────────

    def load_sprite(self, name: str, path: str, size: tuple) -> None:
        try:
            img = pygame.image.load(path).convert_alpha()
            self.sprite_cache[name] = pygame.transform.scale(img, size)
        except Exception:
            pass  # fallback vẽ shape nếu thiếu asset

    def _load_player_animations(self) -> None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        satyr_sheet = os.path.join(
            root_dir, "assets", "sprites", "SATYR_sprite_sheet", "SPRITE_SHEET.png")
        if os.path.exists(satyr_sheet):
            self._load_satyr_player_animations(satyr_sheet)
            if self.player_animations:
                return

        self.player_frame_size = 128
        sprite_dir = os.path.join(
            root_dir, "assets", "sprites", "male_hero_free", "individual_sheets")
        sheets = {
            "idle": "male_hero-idle.png",
            "run": "male_hero-run.png",
            "dash_forward": "male_hero-jump.png",
            "dash_back": "male_hero-jump.png",
            "hurt": "male_hero-fall.png",
        }
        for anim_name, filename in sheets.items():
            frames = self._slice_player_sheet(os.path.join(sprite_dir, filename))
            if frames:
                self.player_animations[anim_name] = frames

    def _load_satyr_player_animations(self, path: str) -> None:
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception:
            return

        frame_size = 32
        self.player_frame_size = frame_size
        self.player_animations["idle"] = self._slice_player_row(sheet, 0, 0, 6, frame_size)
        self.player_animations["run"] = self._slice_player_row(sheet, 1, 0, 8, frame_size)
        row9 = self._slice_player_row(sheet, 8, 0, 6, frame_size)
        self.player_animations["dash_forward"] = row9[:3] or self._slice_player_row(sheet, 2, 0, 4, frame_size)
        self.player_animations["dash_back"] = row9[3:6] or self._slice_player_row(sheet, 2, 0, 4, frame_size)
        self.player_animations["die"] = self._slice_player_row(sheet, 6, 0, 10, frame_size)
        self.player_animations["hurt"] = self._slice_player_row(sheet, 7, 0, 4, frame_size)
        self.player_animations = {
            name: frames for name, frames in self.player_animations.items()
            if frames
        }

    def _slice_player_row(
        self,
        sheet: pygame.Surface,
        row: int,
        start_col: int,
        frame_count: int,
        frame_size: int,
    ) -> list[pygame.Surface]:
        frames = []
        for i in range(frame_count):
            rect = pygame.Rect(
                (start_col + i) * frame_size,
                row * frame_size,
                frame_size,
                frame_size,
            )
            if rect.right > sheet.get_width() or rect.bottom > sheet.get_height():
                break
            frame = sheet.subsurface(rect).copy()
            if frame.get_bounding_rect().width <= 0:
                continue
            frames.append(pygame.transform.scale(frame, self.player_draw_size))
        return frames

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
        frost_root = os.path.join(
            root_dir, "assets", "sprites",
            "Pixel Art VFX - Frost Knight - FREE Version")
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
            "ice_spike": {
                "folder": os.path.join(frost_root, "VFX3", "Frames"),
                "size": (256, 128),
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
            [name for name in os.listdir(folder) if name.lower().endswith(".png")],
            key=self._frame_sort_key)
        frames = []
        for filename in frame_files:
            path = os.path.join(folder, filename)
            try:
                frame = pygame.image.load(path).convert_alpha()
            except Exception:
                continue
            frames.append(pygame.transform.scale(frame, size))
        return frames

    def _frame_sort_key(self, filename: str) -> tuple:
        stem = os.path.splitext(filename)[0]
        parts = "".join(ch if ch.isdigit() else " " for ch in stem).split()
        return tuple(int(part) for part in parts) or (0,)

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

    def draw_map_decorations(
        self,
        cam_x: float,
        cam_y: float,
        min_sort_y: float | None = None,
        max_sort_y: float | None = None,
    ) -> None:
        if self.world_map and hasattr(self.world_map, "draw_decorations"):
            self.world_map.draw_decorations(
                self.screen,
                cam_x,
                cam_y,
                SCREEN_W,
                SCREEN_H,
                self.zoom,
                min_sort_y=min_sort_y,
                max_sort_y=max_sort_y,
            )

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
        if not getattr(player, "alive", True):
            return "die"
        if getattr(player, "hurt_timer", 0.0) > 0:
            return "hurt"
        if getattr(player, "dash_timer", 0.0) > 0:
            return "dash_forward" if getattr(player, "last_dash_forward", True) else "dash_back"
        return "run" if getattr(player, "is_moving", False) else "idle"

    def _get_player_frame_idx(self, anim_name: str, frame_count: int, player) -> int:
        now = pygame.time.get_ticks()
        if anim_name != self.player_anim_state:
            self.player_anim_state = anim_name
            self.player_anim_started_ms = now

        elapsed = max(0, now - self.player_anim_started_ms)
        frame_ms = self._get_player_frame_ms(anim_name, player)
        if anim_name == "die":
            return min(elapsed // frame_ms, frame_count - 1)
        return (elapsed // frame_ms) % frame_count

    def _get_player_frame_ms(self, anim_name: str, player) -> int:
        if anim_name == "run":
            speed_ratio = getattr(player, "move_speed_ratio", 1.0)
            return max(55, int(95 - 30 * speed_ratio))
        if anim_name in ("dash_forward", "dash_back"):
            return 55
        if anim_name == "hurt":
            return 80
        if anim_name == "die":
            return 110
        return 120

    def _get_player_bob(self, anim_name: str) -> int:
        if anim_name != "run":
            return 0
        elapsed = max(0, pygame.time.get_ticks() - self.player_anim_started_ms)
        return int(math.sin(elapsed / 85.0) * self.zoom)

    def draw_enemy(self, enemy, cam_x, cam_y) -> None:
        from logic.entities.sheep import Sheep
        if isinstance(enemy, Sheep):
            self.draw_sheep(enemy, cam_x, cam_y)
            return

        sx, sy = self.world_to_screen(enemy.x, enemy.y, cam_x, cam_y)

        # Status halo (vòng màu bên ngoài)
        self._draw_status_halo(enemy, sx, sy)

        # Xác định logic hoạt hoạ (Animation)
        state = getattr(enemy, 'state', 'run')
        anim_name = 'run'
        from logic.entities.ranged_enemy import RangedEnemy
        from logic.entities.fast_enemy import FastEnemy
        from logic.entities.tank_enemy import TankEnemy
        is_ranged = isinstance(enemy, RangedEnemy)
        is_fast = isinstance(enemy, FastEnemy)
        is_tank = isinstance(enemy, TankEnemy)
        
        if state == 'die':
            anim_name = 'die'
        elif getattr(enemy, 'hurt_timer', 0.0) > 0:
            anim_name = 'hit'
        elif state == 'attack' or state == 'attack1':
            anim_name = 'attack1' if is_fast else 'attack'
        elif state == 'cooldown' or getattr(enemy, 'cast_lock_timer', 0.0) > 0:
            anim_name = 'idle'
        elif state == 'windup':
            anim_name = 'attack2' if is_fast else 'idle'
        elif state == 'lunge':
            anim_name = 'attack2' if is_fast else 'run'
            
        # Ranged Enemy stop moving logic fallback to idle
        if is_ranged and anim_name == 'run':
            dist = math.hypot(enemy.x - cam_x, enemy.y - cam_y) # just approx
            if getattr(enemy, 'cast_lock_timer', 0.0) > 0:
                anim_name = 'idle'

        if is_ranged:
            frames = getattr(self, 'ranged_animations', {}).get(anim_name)
        elif is_fast:
            frames = getattr(self, 'fast_animations', {}).get(anim_name)
        elif is_tank:
            frames = getattr(self, 'tank_animations', {}).get(anim_name)
        else:
            frames = getattr(self, 'mushroom_animations', {}).get(anim_name)
            
        if (type(enemy).__name__ == "Enemy" or is_ranged or is_fast or is_tank) and frames:
            # Sprite cho Enemy thường, Ranged, Fast hoặc Tank
            frame_count = len(frames)
            if anim_name == 'die':
                timer = getattr(enemy, 'die_timer', 0.0)
                idx = min(frame_count - 1, int((timer / 1.2) * frame_count))
            elif anim_name in ('hit', 'idle', 'run'):
                idx = (pygame.time.get_ticks() // 80) % frame_count
            elif state == 'attack' or state == 'attack1':
                timer = getattr(enemy, 'attack_timer', 0.0)
                duration = getattr(enemy, 'ATTACK1_DURATION', 0.6) if state == 'attack1' else getattr(enemy, 'ATTACK_DURATION', 0.8)
                idx = min(frame_count - 1, int((timer / duration) * frame_count))
            elif state == 'windup' and is_fast:
                timer = getattr(enemy, 'attack_timer', 0.0)
                duration = getattr(enemy, 'WINDUP_DURATION', 0.5)
                idx = min(4, int((timer / duration) * 5))
            elif state == 'lunge' and is_fast:
                timer = getattr(enemy, 'attack_timer', 0.0)
                duration = getattr(enemy, 'LUNGE_DURATION', 0.3)
                idx = 5 + min(5, int((timer / duration) * 6))
            else:
                idx = (pygame.time.get_ticks() // 80) % frame_count
                
            img = self._zoom_surface(frames[idx])
            if getattr(enemy, 'facing_dir', 1) > 0:
                img = pygame.transform.flip(img, True, False)
                
            self.screen.blit(img, img.get_rect(midbottom=(sx, sy + self._zoom_len(20))))
        else:
            # Fallback hình tròn
            color = getattr(enemy, 'COLOR', self.COLOR_ENEMY)
            if is_ranged: color = self.COLOR_RANGED
            radius = self._zoom_len(enemy.radius)
            pygame.draw.circle(self.screen, color, (sx, sy), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 2)

        # HP bar
        hp_offset = self._zoom_len(48)
        bar_w = self._zoom_len(42)
        if is_fast:
            hp_offset = self._zoom_len(34)
            bar_w = self._zoom_len(32)
        elif is_tank:
            hp_offset = self._zoom_len(62)
            bar_w = self._zoom_len(54)
        self._draw_hp_bar(enemy, sx, sy, hp_offset, bar_w=bar_w)

    def draw_sheep(self, sheep, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(sheep.x, sheep.y, cam_x, cam_y)

        state_name = sheep.state  # "idle", "wander", "eating", "die"
        anim_state = state_name if state_name in self.sheep_animations else "idle"
        frames = self.sheep_animations.get(anim_state)
        if frames:
            now = pygame.time.get_ticks()
            frame_ms = 120 if state_name == "eating" else 100
            frame_idx = (now // frame_ms + id(sheep) % len(frames)) % len(frames)
            img = self._zoom_surface(frames[frame_idx], smooth=True)  # smooth=True để giữ viền

            if sheep.facing_dir < 0:
                img = pygame.transform.flip(img, True, False)

            rect = img.get_rect(center=(sx, sy))
            self.screen.blit(img, rect)

            # Cừu chỉ hiển thị HP bar khi bị thương
            if sheep.hp < sheep.max_hp:
                self._draw_hp_bar(
                    sheep, sx, sy, self._zoom_len(38), bar_w=self._zoom_len(34))
        else:
            radius = self._zoom_len(sheep.radius)
            pygame.draw.circle(self.screen, (240, 240, 240), (sx, sy), radius)
            pygame.draw.circle(self.screen, (200, 200, 200), (sx, sy), radius, 2)

    def draw_boss(self, boss, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(boss.x, boss.y, cam_x, cam_y)
        radius = self._zoom_len(boss.radius)

        # AoE vòng cảnh báo
        if boss.aoe_active:
            aoe_r   = self._zoom_len(boss.AOE_RADIUS)
            aoe_surf = pygame.Surface((aoe_r * 2, aoe_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aoe_surf, (255, 50, 50, 55),
                               (aoe_r, aoe_r), aoe_r)
            self.screen.blit(aoe_surf, (sx - aoe_r, sy - aoe_r))
            pygame.draw.circle(self.screen, (255, 80, 80), (sx, sy), aoe_r, 2)

        self._draw_status_halo(boss, sx, sy)

        state = getattr(boss, 'state', '')
        anim_name = 'run'
        if state == 'die':
            anim_name = 'die'
        elif getattr(boss, 'hurt_timer', 0.0) > 0:
            anim_name = 'hit'
        elif getattr(boss, 'aoe_active', False):
            anim_name = 'attack'
        elif getattr(boss, 'is_charging', False):
            anim_name = 'run'
        else:
            anim_name = 'run'

        frames = getattr(self, 'boss_animations', {}).get(anim_name)
        if frames:
            frame_count = len(frames)
            if anim_name == 'die':
                timer = getattr(boss, 'die_timer', 0.0)
                idx = min(frame_count - 1, int((timer / 1.2) * frame_count))
            elif anim_name in ('hit', 'idle', 'run'):
                idx = (pygame.time.get_ticks() // 80) % frame_count
            elif getattr(boss, 'aoe_active', False):
                timer = getattr(boss, 'aoe_timer', 0.0)
                duration = 1.5
                idx = min(frame_count - 1, int(((duration - timer) / duration) * frame_count))
            else:
                idx = (pygame.time.get_ticks() // 80) % frame_count

            img = self._zoom_surface(frames[idx])
            # Hình Golem mặc định hướng trái, lật nếu facing_dir > 0
            if getattr(boss, 'facing_dir', 1) > 0:
                img = pygame.transform.flip(img, True, False)
            self.screen.blit(img, img.get_rect(midbottom=(sx, sy + self._zoom_len(35))))
        else:
            body_color = (255, 120, 0) if getattr(boss, 'is_charging', False) else self.COLOR_BOSS
            pygame.draw.circle(self.screen, body_color, (sx, sy), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 3)

        # HP bar (to hơn)
        self._draw_hp_bar(
            boss, sx, sy, self._zoom_len(96),
            bar_w=self._zoom_len(92), bar_h=self._zoom_len(4),
            color=(200, 0, 220))

    def draw_bullet(self, bullet, cam_x, cam_y, dt: float = 0.0) -> None:
        sx, sy      = self.world_to_screen(bullet.x, bullet.y, cam_x, cam_y)
        visual_type = getattr(bullet, 'visual_type', 'circle')
        is_crit     = getattr(bullet, 'is_crit', False)

        sprite_key = {'fire_bolt': 'fire_bolt'}
        if visual_type in sprite_key:
            anim = self._bullet_pool.update_and_get(bullet, dt)
            if anim:
                frame  = anim.current_frame()
                bw, bh = VFX_DISPLAY_SIZE[sprite_key[visual_type]]
                size   = (self._zoom_len(bw), self._zoom_len(bh))
                scaled = pygame.transform.scale(frame, size)
                angle  = math.degrees(math.atan2(-bullet.vy, bullet.vx))
                rotated = pygame.transform.rotate(scaled, angle)
                self.screen.blit(rotated, rotated.get_rect(center=(sx, sy)))
                if is_crit:
                    pygame.draw.circle(self.screen, (255, 180, 40), (sx, sy), self._zoom_len(9), 2)
                return

        if visual_type == 'wind_boomerang':
            # Glow halo để phân biệt với nền đất
            glow_r = self._zoom_len(24)
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (140, 255, 180, 110), (glow_r, glow_r), glow_r)
            pygame.draw.circle(glow_surf, (200, 255, 220, 60),  (glow_r, glow_r), glow_r // 2)
            self.screen.blit(glow_surf, glow_surf.get_rect(center=(sx, sy)))

            frames = getattr(self, 'wind_projectile_frames', [])
            if frames:
                frame_idx = (pygame.time.get_ticks() // 80) % len(frames)
                frame = frames[frame_idx]
                size = self._zoom_len(38)
                scaled = pygame.transform.scale(frame, (size, size))
                angle = math.degrees(math.atan2(-bullet.vy, bullet.vx))
                spin  = getattr(bullet, 'spin_angle', 0.0)
                rotated = pygame.transform.rotate(scaled, angle + spin)
                self.screen.blit(rotated, rotated.get_rect(center=(sx, sy)))
            else:
                pygame.draw.circle(self.screen, (140, 255, 180), (sx, sy),
                                   self._zoom_len(bullet.radius))
            if is_crit:
                pygame.draw.circle(self.screen, (200, 255, 200), (sx, sy),
                                   self._zoom_len(16), 2)
            return

        if visual_type == 'sword_beam':
            self._draw_sword_blade(bullet, sx, sy, cam_x, cam_y, is_crit)
            return

        colors = {
            'circle': (255, 255, 100),
            'fire_ball': (255, 100, 30),
            'wind_ball': (100, 220, 255),
        }
        color = colors.get(visual_type, self.COLOR_BULLET)
        if is_crit:
            color = tuple(min(255, c + 70) for c in color)
        radius = self._zoom_len(bullet.radius + (3 if is_crit else 0))
        pygame.draw.circle(self.screen, color, (sx, sy), radius)
        if is_crit:
            pygame.draw.circle(self.screen, (255, 200, 50), (sx, sy), radius, 2)
        elif visual_type in ('fire_ball', 'wind_ball'):
            ring = (255, 200, 50) if visual_type == 'fire_ball' else (200, 240, 255)
            pygame.draw.circle(self.screen, ring, (sx, sy), radius + self._zoom_len(2), 1)

    def _draw_sword_blade(self, bullet, sx, sy, cam_x, cam_y, is_crit) -> None:
        """Flash of Swords — 1 lưỡi kiếm MẢNH kiểu pixel: gốc mọc ra từ NGUỒN
        (viên đạn / điểm cuối tia, bullet.player_x/player_y), thân hơi cong,
        THUÔN NHỌN dần về mũi (không có đầu tròn). Mũi = vị trí bullet hiện tại
        (sx, sy) đang quét quanh nguồn."""
        ox = getattr(bullet, 'player_x', bullet.x)
        oy = getattr(bullet, 'player_y', bullet.y)
        bx, by = self.world_to_screen(ox, oy, cam_x, cam_y)   # gốc kiếm (ở đạn/nguồn)
        tx, ty = sx, sy                                       # mũi kiếm
        dx, dy = tx - bx, ty - by
        length = math.hypot(dx, dy)
        if length < 2:
            return
        ux, uy = dx / length, dy / length     # dọc theo lưỡi
        px, py = -uy, ux                       # vuông góc lưỡi

        blade_color = (255, 232, 150) if is_crit else (196, 230, 255)
        core_color  = (255, 255, 225) if is_crit else (240, 250, 255)
        glow_color  = (255, 210, 90)  if is_crit else (150, 205, 255)
        half_w = max(1.5, self._zoom_len(2.6))   # bề rộng NỬA lưỡi — mảnh
        curve  = self._zoom_len(5.0)             # độ cong nhẹ của lưỡi
        N = 12

        # Dựng 2 mép lưỡi: rộng nhất ~giữa, thon nhọn dần về 2 đầu (mũi = điểm).
        left, right, spine = [], [], []
        for i in range(N + 1):
            t = i / N
            w   = half_w * (math.sin(math.pi * t) ** 0.65)   # thon 2 đầu
            bow = curve * math.sin(math.pi * t)              # cong 1 phía
            cxp = bx + ux * (length * t) + px * bow
            cyp = by + uy * (length * t) + py * bow
            spine.append((cxp, cyp))
            left.append((cxp + px * w, cyp + py * w))
            right.append((cxp - px * w, cyp - py * w))
        poly = left + right[::-1]

        # Quầng sáng mờ quanh lưỡi (vẽ trên surface cục bộ theo bbox lưỡi).
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        pad = int(self._zoom_len(6)) + 2
        minx, miny = int(min(xs)) - pad, int(min(ys)) - pad
        w_s = int(max(xs)) + pad - minx
        h_s = int(max(ys)) + pad - miny
        if 0 < w_s < 400 and 0 < h_s < 400:
            glow = pygame.Surface((w_s, h_s), pygame.SRCALPHA)
            pygame.draw.line(glow, (*glow_color, 70), (bx - minx, by - miny),
                             (tx - minx, ty - miny), max(3, self._zoom_len(6)))
            self.screen.blit(glow, (minx, miny))

        # Thân lưỡi + gân sáng giữa (không đầu tròn).
        pygame.draw.polygon(self.screen, blade_color, poly)
        if len(spine) >= 2:
            pygame.draw.lines(self.screen, core_color, False, spine,
                              max(1, self._zoom_len(1)))

    def draw_enemy_bullet(self, eb, cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(eb.x, eb.y, cam_x, cam_y)
        pygame.draw.circle(self.screen, self.COLOR_ENEMY_BULLET, (sx, sy), self._zoom_len(eb.radius))

    def draw_xp_orb(self, orb, cam_x, cam_y) -> None:
        from logic.entities.meat import Meat
        if isinstance(orb, Meat):
            self.draw_meat(orb, cam_x, cam_y)
            return

        now = pygame.time.get_ticks()
        bob = math.sin(now * 0.006 + id(orb) % 37) * self._zoom_len(2.0)
        sx, sy = self.world_to_screen(orb.x, orb.y, cam_x, cam_y)
        sy += int(bob)

        # Vẽ Gold Resource Highlight động
        if self.gold_orb_frames:
            # frame_idx lặp từ 0 đến 5 dựa trên ticks
            frame_idx = (now // 110 + id(orb) % 6) % len(self.gold_orb_frames)
            frame = self.gold_orb_frames[frame_idx]
            
            value = getattr(orb, "value", 1)
            # Thu nhỏ lại cho bằng kích thước exp (~28x28 base, scale theo zoom camera và giá trị)
            base_size = 28.0 * (1.0 + min(0.18, value / 240.0))
            draw_size = max(6, self._zoom_len(base_size))
            
            # Cache scaled image để cải thiện hiệu năng
            cache_key = (id(frame), draw_size)
            scaled_img = self.scaled_cache.get(cache_key)
            if scaled_img is None:
                # Dùng smoothscale để giữ nguyên viền khi scale nhỏ
                scaled_img = pygame.transform.smoothscale(frame, (draw_size, draw_size))
                self.scaled_cache[cache_key] = scaled_img

            rect = scaled_img.get_rect(center=(sx, sy))
            self.screen.blit(scaled_img, rect)
        else:
            # Fallback đa giác nếu thiếu ảnh
            value = getattr(orb, "value", 1)
            if value >= 80:
                core = (255, 235, 120)
                edge = (255, 170, 75)
            elif value >= 25:
                core = (160, 135, 255)
                edge = (95, 205, 255)
            else:
                core = (145, 255, 185)
                edge = (60, 210, 190)

            size = max(3, self._zoom_len(orb.radius * 0.46 * (1.0 + min(0.18, value / 240.0))))
            points = [
                (sx, sy - size),
                (sx + int(size * 0.58), sy),
                (sx, sy + size),
                (sx - int(size * 0.58), sy),
            ]
            pygame.draw.polygon(self.screen, edge, points)
            inner = [
                (sx, sy - max(1, int(size * 0.55))),
                (sx + max(1, int(size * 0.30)), sy),
                (sx, sy + max(1, int(size * 0.55))),
                (sx - max(1, int(size * 0.30)), sy),
            ]
            pygame.draw.polygon(self.screen, core, inner)
            if size >= 4:
                pygame.draw.line(
                    self.screen,
                    (245, 255, 235),
                    (sx, sy - max(1, size // 2)),
                    (sx + max(1, size // 4), sy - max(1, size // 4)),
                    1,
                )

    def draw_meat(self, meat, cam_x, cam_y) -> None:
        now = pygame.time.get_ticks()
        bob = math.sin(now * 0.006 + id(meat) % 37) * self._zoom_len(2.0)
        sx, sy = self.world_to_screen(meat.x, meat.y, cam_x, cam_y)
        sy += int(bob)

        if self.meat_sprite:
            draw_size = self._zoom_len(26)
            cache_key = (id(self.meat_sprite), draw_size)
            scaled_img = self.scaled_cache.get(cache_key)
            if scaled_img is None:
                # Dùng smoothscale để giữ nguyên viền khi scale nhỏ
                scaled_img = pygame.transform.smoothscale(self.meat_sprite, (draw_size, draw_size))
                self.scaled_cache[cache_key] = scaled_img

            rect = scaled_img.get_rect(center=(sx, sy))
            self.screen.blit(scaled_img, rect)
        else:
            radius = self._zoom_len(meat.radius)
            pygame.draw.circle(self.screen, (180, 80, 50), (sx, sy), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), radius, 1)

    def draw_ice_charge_preview(self, ice_charge: dict, cam_x, cam_y) -> None:
        attacks = ice_charge.get("attacks") if ice_charge else None
        if not attacks:
            return
        ratio = max(0.0, min(1.0, ice_charge.get("ratio", 0.0)))
        for attack in attacks:
            self._draw_ice_hitbox_preview(attack, ratio, cam_x, cam_y)

    def _draw_ice_hitbox_preview(self, attack: dict, ratio: float, cam_x, cam_y) -> None:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fill = (95, 205, 255, int(45 + 70 * ratio))
        outline = (190, 245, 255, int(140 + 90 * ratio))

        if attack.get("is_spiral"):
            cx, cy = self.world_to_screen(attack["start_x"], attack["start_y"], cam_x, cam_y)
            orbit_radius = self._zoom_len(attack["radius"])
            arc_length_rad = attack["arc_length_rad"]
            start_angle = attack["aim_angle"] - arc_length_rad / 2
            
            thickness = self._zoom_len(78.0)
            inner_r = orbit_radius - thickness / 2
            outer_r = orbit_radius + thickness / 2
            
            steps = max(6, int(math.degrees(arc_length_rad) / 10))
            points = []
            
            # Quét vòng ngoài
            for i in range(steps + 1):
                angle = start_angle + (i / steps) * arc_length_rad
                bx = cx + math.cos(angle) * outer_r
                by = cy + math.sin(angle) * outer_r
                points.append((bx, by))
                
            # Quét vòng trong
            for i in range(steps, -1, -1):
                angle = start_angle + (i / steps) * arc_length_rad
                bx = cx + math.cos(angle) * inner_r
                by = cy + math.sin(angle) * inner_r
                points.append((bx, by))
                
            if len(points) >= 3:
                pygame.draw.polygon(overlay, fill, points)
                pygame.draw.polygon(overlay, outline, points, max(2, self._zoom_len(2)))
            
            self.screen.blit(overlay, (0, 0))
            return

        points = [
            self.world_to_screen(x, y, cam_x, cam_y)
            for x, y in attack.get("corners", [])
        ]
        if len(points) < 3:
            return

        pygame.draw.polygon(overlay, fill, points)
        pygame.draw.polygon(overlay, outline, points, max(2, self._zoom_len(2)))

        sx, sy = self.world_to_screen(attack["start_x"], attack["start_y"], cam_x, cam_y)
        ex, ey = self.world_to_screen(attack["end_x"], attack["end_y"], cam_x, cam_y)
        pygame.draw.line(
            overlay,
            (230, 255, 255, int(120 + 90 * ratio)),
            (sx, sy),
            (ex, ey),
            max(2, self._zoom_len(3)),
        )
        self.screen.blit(overlay, (0, 0))

    def draw_effects(self, effects: list[dict], cam_x, cam_y) -> None:
        for effect in effects:
            anim_key = effect.get('kind')
            # ice_spiral dùng chung bộ hình ảnh (frames) với ice_spike
            if anim_key == 'ice_spiral':
                anim_key = 'ice_spike'
                
            frames = self.effect_animations.get(anim_key)
            if not frames:
                continue
            glow_frames = self.effect_glow_animations.get(anim_key)

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
            if effect.get('kind') == 'ice_spike':
                self._draw_ice_spike_effect(effect, frames, cam_x, cam_y)
                continue
            if effect.get('kind') == 'ice_spiral':
                self._draw_ice_spiral_effect(effect, frames, cam_x, cam_y)
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

    def draw_active_effect(self, effect, cam_x, cam_y, dt: float = 0.0) -> None:
        vt = getattr(effect, 'visual_type', '')
        if vt == 'blood_impact':
            self._draw_center_sprite_effect(effect, cam_x, cam_y, dt, 'blood_impact')
        elif vt == 'fire_bolt_hit':
            self._draw_center_sprite_effect(effect, cam_x, cam_y, dt, 'fire_bolt_hit')
        elif vt == 'fire_explosion':
            self._draw_center_sprite_effect(effect, cam_x, cam_y, dt, 'fire_explosion', aoe=True)
        elif vt == 'air_explosion':
            self._draw_center_sprite_effect(effect, cam_x, cam_y, dt, 'air_explosion', aoe=True)
        elif vt == 'air_burst':
            self._draw_directional_sprite_effect(effect, cam_x, cam_y, dt, 'air_burst')
        elif vt == 'fire_breath_jet':
            self._draw_fire_jet(effect, cam_x, cam_y, dt)
        elif vt == 'wind_vortex':
            self._draw_vortex_zone(effect, cam_x, cam_y)

    def _draw_center_sprite_effect(self, effect, cam_x, cam_y, dt: float,
                                   key: str, aoe: bool = False) -> None:
        sx, sy = self.world_to_screen(effect.x, effect.y, cam_x, cam_y)
        total = getattr(effect, 'TOTAL_LIFE', getattr(effect, 'LIFETIME', 0.8))
        t = min(1.0, effect.elapsed / total) if total > 0 else 1.0
        if aoe:
            radius = self._zoom_len(getattr(effect, 'AoE_RADIUS', 120))
            color = (255, 120, 30) if key == 'fire_explosion' else (160, 230, 160)
            alpha = int(160 * (1.0 - t))
            if alpha > 0 and radius > 0:
                ring = pygame.Surface((radius * 2 + 18, radius * 2 + 18), pygame.SRCALPHA)
                grow = min(1.0, t / 0.4)
                rr = max(1, int(radius * grow))
                pygame.draw.circle(ring, (*color, alpha), (radius + 9, radius + 9), rr, 7)
                self.screen.blit(ring, (sx - radius - 9, sy - radius - 9))

        anim = self._effect_pool.update_and_get(effect, dt)
        if not anim:
            return
        frame = anim.current_frame()
        base_w, base_h = VFX_DISPLAY_SIZE.get(key, (80, 80))
        if aoe:
            size = self._zoom_len(getattr(effect, 'AoE_RADIUS', base_w / 2) * 2.1)
            draw_size = (size, size)
        else:
            draw_size = (self._zoom_len(base_w), self._zoom_len(base_h))
        scaled = pygame.transform.scale(frame, draw_size)
        if t > 0.55:
            scaled.set_alpha(max(0, int(255 * (1.0 - (t - 0.55) / 0.45))))
        self.screen.blit(scaled, scaled.get_rect(center=(sx, sy)))

    def _draw_directional_sprite_effect(self, effect, cam_x, cam_y, dt: float,
                                        key: str) -> None:
        sx, sy = self.world_to_screen(effect.x, effect.y, cam_x, cam_y)
        total = getattr(effect, 'lifetime', getattr(effect, 'LIFETIME', 0.4))
        t = min(1.0, effect.elapsed / total) if total > 0 else 1.0
        anim = self._effect_pool.update_and_get(effect, dt)
        if not anim:
            color = (150, 230, 150)
            radius = self._zoom_len(getattr(effect, 'hit_radius', 28))
            pygame.draw.circle(self.screen, color, (sx, sy), radius, 2)
            return

        frame = anim.current_frame()
        base_w, base_h = VFX_DISPLAY_SIZE.get(key, (110, 110))
        scale = 1.0 + getattr(effect, 'charge_ratio', 0.0) * 0.8
        dw = self._zoom_len(base_w * scale)
        dh = self._zoom_len(base_h * scale)
        scaled = pygame.transform.scale(frame, (dw, dh))
        if t > 0.6:
            scaled.set_alpha(max(0, int(255 * (1.0 - (t - 0.6) / 0.4))))
        rotated = pygame.transform.rotate(scaled, -math.degrees(effect.angle_rad))
        self.screen.blit(rotated, rotated.get_rect(center=(sx, sy)))

    def _draw_fire_jet(self, jet, cam_x, cam_y, dt: float) -> None:
        sx, sy = self.world_to_screen(jet.x, jet.y, cam_x, cam_y)
        length = self._zoom_len(max(40.0, jet.length))
        width = self._zoom_len(max(34.0, jet.length * 0.34))
        angle = jet.angle_rad
        cx = sx + math.cos(angle) * length / 2
        cy = sy + math.sin(angle) * length / 2
        anim = self._effect_pool.update_and_get(jet, dt)
        if not anim:
            end = (sx + math.cos(angle) * length, sy + math.sin(angle) * length)
            pygame.draw.line(self.screen, (255, 130, 30), (sx, sy), end, max(3, width // 5))
            return
        frame = anim.current_frame()
        scaled = pygame.transform.scale(frame, (length, width))
        rotated = pygame.transform.rotate(scaled, -math.degrees(angle))
        self.screen.blit(rotated, rotated.get_rect(center=(int(cx), int(cy))))

    def _draw_vortex_zone(self, effect, cam_x, cam_y) -> None:
        """Cơn lốc Perfect Storm — vòng tròn mờ đánh dấu vùng hút + các vệt
        gió xoáy quay quanh tâm. Tâm dùng effect.x/effect.y HIỆN TẠI (không
        phải điểm cast gốc) vì VortexZone tự lượn qua lại mỗi frame."""
        sx, sy = self.world_to_screen(effect.x, effect.y, cam_x, cam_y)
        radius = self._zoom_len(effect.AoE_RADIUS)
        if radius < 1:
            return
        color = (120, 230, 150)

        grow = min(1.0, effect.elapsed / max(0.001, effect.GROW_DUR))
        t = effect.anim_progress
        fade_from = 0.7
        fade = 1.0 if t < fade_from else max(0.0, 1.0 - (t - fade_from) / (1.0 - fade_from))
        r = max(1, int(radius * grow))

        ring = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*color, int(140 * fade)), (r + 4, r + 4), r, 3)
        self.screen.blit(ring, (sx - r - 4, sy - r - 4))

        # 3 vệt xoáy, mỗi vệt 4 chấm cuộn dần vào tâm — bán quay riêng biệt
        # với chuyển động lượn qua lại của cả vùng (spin nhanh hơn hẳn).
        spin = effect.elapsed * 3.0
        for i in range(3):
            base_ang = spin + i * (math.tau / 3)
            for k in range(4):
                frac = (k + 1) / 5.0
                wr = r * frac * grow
                ang = base_ang + frac * 2.4
                wx = sx + math.cos(ang) * wr
                wy = sy + math.sin(ang) * wr
                dot_r = max(1, self._zoom_len(3 * (1.0 - frac * 0.5)))
                pygame.draw.circle(self.screen, color, (int(wx), int(wy)), dot_r)

    def draw_wind_charge(self, player, ratio: float, cam_x, cam_y) -> None:
        ratio = max(0.0, min(1.0, ratio))
        sx, sy = self.world_to_screen(player.x, player.y, cam_x, cam_y)
        radius = self._zoom_len(18 + ratio * 78)
        base = pygame.time.get_ticks() * 0.005
        count = 4 + int(ratio * 10)
        color = (170, 235, 175) if ratio < 0.66 else (220, 255, 220)
        for i in range(count):
            angle = base + i * (math.tau / count)
            rad = radius * (0.55 + 0.45 * math.sin(base * 2.0 + i))
            px = sx + math.cos(angle) * rad
            py = sy + math.sin(angle) * rad
            pygame.draw.circle(self.screen, color, (int(px), int(py)),
                               max(2, self._zoom_len(2 + ratio * 3)))
        ring = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        alpha = int(90 + 130 * ratio)
        pygame.draw.circle(ring, (150, 240, 170, alpha), (radius + 4, radius + 4), radius, 3)
        self.screen.blit(ring, (sx - radius - 4, sy - radius - 4))

    def _draw_ice_spiral_effect(self, effect: dict, frames: list[pygame.Surface], cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(effect['cx'], effect['cy'], cam_x, cam_y)
        orbit_radius = self._zoom_len(effect['radius'])
        if orbit_radius < 1:
            return

        arc_length_rad = effect['arc_length_rad']
        arc_len = orbit_radius * arc_length_rad
        if arc_len <= 0:
            return

        # Chiều cao (độ dày) của băng
        target_h = max(4, self._zoom_len(78.0))

        # 1. Tạo dải băng thẳng đã có sẵn animation trồi lên theo thời gian (age)
        tiled_surf, _pad = self._tile_ice_spike_frames(frames, int(arc_len), target_h, effect.get('age', 0.0))
        
        # 2. Bẻ cong dải băng thành cung tròn bao quanh nhân vật
        start_angle = effect['aim_angle'] - arc_length_rad / 2
        N = max(32, int(arc_len / 5))
        
        for i in range(N):
            t = (i + 0.5) / N
            x0 = int(i * arc_len / N)
            x1 = int((i + 1) * arc_len / N)
            sw = max(1, x1 - x0)
            
            # Đảm bảo không cắt lố ảnh
            if x0 >= tiled_surf.get_width():
                continue
            sw = min(sw, tiled_surf.get_width() - x0)
            if sw < 1:
                continue
                
            angle = start_angle + t * arc_length_rad
            bx = sx + math.cos(angle) * orbit_radius
            by = sy + math.sin(angle) * orbit_radius
            tangent_deg = math.degrees(angle) + 90

            strip = tiled_surf.subsurface((x0, 0, sw, tiled_surf.get_height()))
            # Thêm 2px bề ngang để nối mí chồng lên nhau khít hoàn toàn
            scaled = pygame.transform.smoothscale(strip, (sw + 2, target_h))
            rotated = pygame.transform.rotate(scaled, -tangent_deg)
            rect = rotated.get_rect(center=(int(bx), int(by)))
            self.screen.blit(rotated, rect)

    def _draw_ice_spike_effect(self, effect: dict, frames: list[pygame.Surface], cam_x, cam_y) -> None:
        sx, sy = self.world_to_screen(effect['x'], effect['y'], cam_x, cam_y)
        ex, ey = self.world_to_screen(effect['x2'], effect['y2'], cam_x, cam_y)
        dx = ex - sx
        dy = ey - sy
        length = max(1, int(math.hypot(dx, dy)))
        height = self._zoom_len(effect.get('width', 90))
        img, pad = self._tile_ice_spike_frames(frames, length, height, effect.get('age', 0.0))
        angle = -math.degrees(math.atan2(dy, dx))
        if dx < 0:
            img = pygame.transform.flip(img, True, False)
            angle += 180
        img = pygame.transform.rotate(img, angle)
        # Canvas dài thêm `pad` về phía đầu mút → dời tâm nửa pad theo hướng bắn
        # để gốc spike vẫn nằm đúng ở người (không lệch về sau).
        ux, uy = dx / length, dy / length
        cx = (sx + ex) / 2 + ux * pad / 2
        cy = (sy + ey) / 2 + uy * pad / 2
        rect = img.get_rect(center=(int(cx), int(cy)))
        self.screen.blit(img, rect)

    def _tile_ice_spike_frames(
        self,
        frames: list[pygame.Surface],
        length: int,
        height: int,
        age: float,
    ) -> tuple[pygame.Surface, int]:
        if length <= 0 or height <= 0:
            return pygame.Surface((1, 1), pygame.SRCALPHA), 0
        if not frames:
            return pygame.Surface((length, height), pygame.SRCALPHA), 0

        bounds_list = [frame.get_bounding_rect() for frame in frames]
        valid_bounds = [bounds for bounds in bounds_list if bounds.width > 0 and bounds.height > 0]
        if not valid_bounds:
            return pygame.Surface((length, height), pygame.SRCALPHA), 0

        max_bounds_w = max(bounds.width for bounds in valid_bounds)
        scale = height / max(1, frames[0].get_height())
        base_segment_w = max(1, int(max_bounds_w * scale))
        advance = max(1, int(base_segment_w * 0.38))
        chunk_delay = 0.045
        chunk_anim = 0.30
        chunk_fade = 0.16
        # Vùng đệm cuối canvas để segment chót vẽ TRỌN (không bị cắt phẳng ở đầu mút)
        pad = base_segment_w + 2
        canvas = pygame.Surface((length + pad, height), pygame.SRCALPHA)

        x = 0
        chunk_idx = 0
        while x < length:
            local_age = age - chunk_idx * chunk_delay
            if local_age < 0:
                break
            if local_age > chunk_anim + chunk_fade:
                x += advance
                chunk_idx += 1
                continue

            frame_idx = min(int((local_age / chunk_anim) * len(frames)), len(frames) - 1)
            frame = frames[frame_idx]
            bounds = bounds_list[frame_idx]
            if bounds.width <= 0 or bounds.height <= 0:
                x += advance
                chunk_idx += 1
                continue

            cropped = frame.subsurface((bounds.left, 0, bounds.width, frame.get_height())).copy()
            segment_w = max(1, int(cropped.get_width() * scale))
            segment = pygame.transform.scale(cropped, (segment_w, height))
            if local_age > chunk_anim:
                alpha = max(0, min(255, int(255 * (1.0 - (local_age - chunk_anim) / chunk_fade))))
                segment.set_alpha(alpha)

            # Blit trọn segment (canvas đã có vùng đệm `pad` nên không bị cắt)
            canvas.blit(segment, (x, 0))
            x += advance
            chunk_idx += 1
        return canvas, pad

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
        if effect.get('vortex'):
            self._draw_vortex_beam(sx, sy, ex, ey, frame, glow_frame, effect.get('fixed_size', False))
        else:
            self._draw_straight_beam(sx, sy, ex, ey, frame, glow_frame, effect.get('fixed_size', False))

    def _draw_vortex_beam(
        self,
        sx: int, sy: int,
        ex: int, ey: int,
        frame: pygame.Surface | None,
        glow_frame: pygame.Surface | None,
        is_primary: bool = False,
    ) -> None:
        """
        Vẽ vortex ring: vòng cung tròn (~315°) bao quanh player (sx,sy).
        ex,ey xác định bán kính và vị trí khoảng hở.
        PNG được cắt thành 64 strips, mỗi strip rotate theo tangent đường tròn.
        """
        dx = ex - sx
        dy = ey - sy
        orbit_radius = math.hypot(dx, dy)
        if orbit_radius < 1 or frame is None:
            return

        # Bán kính vòng cung và cung độ
        gap_angle = math.atan2(dy, dx)
        GAP       = 0.7             # ~40° khoảng hở
        ARC       = math.tau - GAP  # ~320° cung tròn
        arc_len   = orbit_radius * ARC
        N         = max(32, int(arc_len / 5))  # Cứ 5px cắt 1 mảnh để mượt

        frame_w = frame.get_width()
        frame_h = frame.get_height()
        target_h = max(4, self._zoom_len(int(frame_h * 0.55)))

        def _blit_slices(src: pygame.Surface, flags: int = 0) -> None:
            # TỰ ĐỘNG CẮT BỎ VIỀN TRONG SUỐT Ở HAI ĐẦU CỦA ẢNH GỐC
            bounds = src.get_bounding_rect()
            if bounds.width < 1 or bounds.height < 1:
                return
            cropped = src.subsurface((bounds.x, 0, bounds.width, src.get_height()))
            cw = cropped.get_width()
            ch = cropped.get_height()

            # Tạo một dải liền mạch (tiled surface) có chiều dài bằng arc_len
            tiled_surf = pygame.Surface((int(arc_len) + cw, ch), pygame.SRCALPHA)
            x_offset = 0
            
            # OVERLAP: Thay vì nối sát mép, ta nối lấn lên nhau 15% để dính liền khối
            advance = max(1, int(cw * 0.85))
            
            while x_offset <= arc_len:
                tiled_surf.blit(cropped, (x_offset, 0), special_flags=pygame.BLEND_RGBA_MAX)
                x_offset += advance

            for i in range(N):
                t = (i + 0.5) / N
                
                # Cắt từ dải liền mạch
                x0 = int(i * arc_len / N)
                x1 = int((i + 1) * arc_len / N)
                sw = max(1, x1 - x0)
                
                angle = gap_angle + GAP / 2 + t * ARC
                bx = sx + math.cos(angle) * orbit_radius
                by = sy + math.sin(angle) * orbit_radius

                tangent_deg = math.degrees(angle) + 90

                strip = tiled_surf.subsurface((x0, 0, sw, ch))
                # Scale bề dọc, giữ nguyên bề ngang (cộng thêm 2px để chồng mép khít hoàn toàn)
                scaled = pygame.transform.smoothscale(strip, (sw + 2, target_h))
                rotated = pygame.transform.rotate(scaled, -tangent_deg)
                rect = rotated.get_rect(center=(int(bx), int(by)))
                self.screen.blit(rotated, rect, special_flags=flags)

        _blit_slices(frame)
        if glow_frame is not None:
            _blit_slices(glow_frame, pygame.BLEND_RGBA_ADD)

    def _draw_straight_beam(
        self,
        sx: int, sy: int,
        ex: int, ey: int,
        frame: pygame.Surface | None,
        glow_frame: pygame.Surface | None,
        is_primary: bool = False
    ) -> None:
        """Vẽ tia lightning gốc bằng cách dùng hình ảnh (VFX) kéo dài từ (sx,sy) đến (ex,ey)."""
        if frame is None:
            return

        dx = ex - sx
        dy = ey - sy
        length = math.hypot(dx, dy)
        if length < 1:
            return

        # Tính góc để xoay ảnh
        angle = math.degrees(math.atan2(-dy, dx))

        # Scale đều (uniform scale) để giữ nguyên tỉ lệ ảnh gốc. 
        # Nhưng trước tiên phải CẮT BỎ viền trong suốt của ảnh gốc để 2 đầu chạm khít
        bounds = frame.get_bounding_rect()
        if bounds.width < 1 or bounds.height < 1:
            return
            
        cropped_frame = frame.subsurface((bounds.x, 0, bounds.width, frame.get_height()))
        cropped_glow = None
        if glow_frame is not None:
            glow_bounds = glow_frame.get_bounding_rect()
            if glow_bounds.width > 0:
                cropped_glow = glow_frame.subsurface((glow_bounds.x, 0, glow_bounds.width, glow_frame.get_height()))

        frame_w = cropped_frame.get_width()
        frame_h = cropped_frame.get_height()
        target_w = int(length)
        target_h = max(1, int(frame_h * (length / frame_w)))

        cx = (sx + ex) / 2
        cy = (sy + ey) / 2

        def _blit_stretched(src: pygame.Surface, flags: int = 0) -> None:
            # Dùng smoothscale để không bị răng cưa khi scale
            scaled = pygame.transform.smoothscale(src, (target_w, target_h))
            rotated = pygame.transform.rotate(scaled, angle)
            rect = rotated.get_rect(center=(int(cx), int(cy)))
            self.screen.blit(rotated, rect, special_flags=flags)

        _blit_stretched(cropped_frame)
        if cropped_glow is not None:
            _blit_stretched(cropped_glow, pygame.BLEND_RGBA_ADD)

    # ── Render tổng ───────────────────────────────────────────────────────────

    def draw_all(self, player, enemies, boss, bullets, xp_orbs,
                 enemy_bullets, cam_x, cam_y,
                 effects=None,
                 ultimate_flash=None,
                 ice_charge=None,
                 active_effects=None,
                 dt: float = 0.0) -> None:
        self.draw_background(cam_x, cam_y)
        player_sort_y = player.y + getattr(player, "radius", 0.0)
        self.draw_map_decorations(cam_x, cam_y, max_sort_y=player_sort_y)
        # Ultimate AoE flash (dưới các entity)
        if ultimate_flash:
            self._draw_ultimate_flash(ultimate_flash, cam_x, cam_y)
        if ice_charge:
            self.draw_ice_charge_preview(ice_charge, cam_x, cam_y)
        if active_effects:
            for effect in active_effects:
                if effect.alive and getattr(effect, 'visual_type', '') == 'air_explosion':
                    self.draw_active_effect(effect, cam_x, cam_y, dt)
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
                self.draw_bullet(bullet, cam_x, cam_y, dt)
        if effects:
            self.draw_effects(effects, cam_x, cam_y)
        if active_effects:
            for effect in active_effects:
                if effect.alive and getattr(effect, 'visual_type', '') != 'air_explosion':
                    self.draw_active_effect(effect, cam_x, cam_y, dt)
        self.draw_player(player, cam_x, cam_y)
        self.draw_map_decorations(cam_x, cam_y, min_sort_y=player_sort_y)

        # Cập nhật dt và sinh lá rơi từ các cây trong tầm nhìn
        now = pygame.time.get_ticks()
        dt = (now - self.last_leave_tick) / 1000.0
        self.last_leave_tick = now
        dt = min(0.1, max(0.0, dt))

        import random as _rnd
        if self.world_map and hasattr(self.world_map, "decorations"):
            view_w = SCREEN_W / (2 * self.zoom)
            view_h = SCREEN_H / (2 * self.zoom)
            view_left = cam_x - view_w - 120
            view_right = cam_x + view_w + 120
            view_top = cam_y - view_h - 120
            view_bottom = cam_y + view_h + 120

            for prop in self.world_map.decorations:
                if prop.get("kind") == "tree":
                    tx = prop["x"]
                    ty = prop["y"]
                    if view_left <= tx <= view_right and view_top <= ty <= view_bottom:
                        if _rnd.random() < 0.04:
                            frames = prop["frames"]
                            frame = frames[0]
                            w = frame.get_width()
                            h = frame.get_height()
                            leaf_x = tx + _rnd.uniform(w * 0.15, w * 0.85)
                            leaf_y = ty + _rnd.uniform(h * 0.1, h * 0.5)
                            self._spawn_leaf(leaf_x, leaf_y)

        self._update_and_draw_leaves(dt, cam_x, cam_y)

        self.draw_minimap(player, enemies, boss, cam_x, cam_y)
        live_bullet_ids = {id(b) for b in bullets if b.alive}
        live_effect_ids = {id(e) for e in (active_effects or []) if e.alive}
        self._bullet_pool.cleanup(live_bullet_ids)
        self._effect_pool.cleanup(live_effect_ids)

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

    def draw_minimap(self, player, enemies, boss, cam_x, cam_y) -> None:
        size = 75
        pad = 5
        x = SCREEN_W - size - pad
        y = 18
        bg = pygame.Surface((size, size), pygame.SRCALPHA)
        bg.fill((10, 18, 20, 185))
        pygame.draw.rect(bg, (90, 120, 110, 220), (0, 0, size, size), 2)

        if self._has_finite_map_bounds():
            self._draw_finite_minimap(bg, player, enemies, boss)
        else:
            self._draw_radar_minimap(bg, player, enemies, boss)

        self.screen.blit(bg, (x, y))

    def _has_finite_map_bounds(self) -> bool:
        return (
            self.world_map is not None
            and hasattr(self.world_map, "origin_x")
            and hasattr(self.world_map, "origin_y")
            and hasattr(self.world_map, "pixel_width")
            and hasattr(self.world_map, "pixel_height")
        )

    def _draw_finite_minimap(self, surface, player, enemies, boss) -> None:
        inset = 8
        map_rect = pygame.Rect(
            inset,
            inset,
            surface.get_width() - inset * 2,
            surface.get_height() - inset * 2,
        )
        minimap = self._get_minimap_surface(map_rect.size)
        surface.blit(minimap, map_rect.topleft)
        pygame.draw.rect(surface, (210, 230, 190, 210), map_rect, 1)

        def project(wx: float, wy: float) -> tuple[int, int]:
            rel_x = (wx - self.world_map.origin_x) / max(1, self.world_map.pixel_width)
            rel_y = (wy - self.world_map.origin_y) / max(1, self.world_map.pixel_height)
            px = map_rect.left + int(max(0.0, min(1.0, rel_x)) * map_rect.width)
            py = map_rect.top + int(max(0.0, min(1.0, rel_y)) * map_rect.height)
            return px, py

        self._draw_minimap_entities(surface, player, enemies, boss, project)

    def _get_minimap_surface(self, size: tuple[int, int]) -> pygame.Surface:
        source_id = (id(self.world_map), size)
        if self.minimap_surface is not None and self.minimap_source_id == source_id:
            return self.minimap_surface

        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((70, 120, 62, 230))
        if hasattr(self.world_map, "layers"):
            tile_w = size[0] / max(1, self.world_map.width)
            tile_h = size[1] / max(1, self.world_map.height)
            for layer in self.world_map.layers:
                for ty in range(layer["height"]):
                    row = ty * layer["width"]
                    for tx in range(layer["width"]):
                        gid = layer["gids"][row + tx]
                        if gid == 0:
                            continue
                        color = self._minimap_gid_color(gid)
                        rect = pygame.Rect(
                            int(tx * tile_w),
                            int(ty * tile_h),
                            max(1, math.ceil(tile_w)),
                            max(1, math.ceil(tile_h)),
                        )
                        pygame.draw.rect(surf, color, rect)

        self.minimap_surface = surf
        self.minimap_source_id = source_id
        return surf

    def _minimap_gid_color(self, gid: int) -> tuple[int, int, int, int]:
        clean_gid = gid & 0x1FFFFFFF
        if clean_gid == 55:
            return (40, 115, 165, 240)
        if clean_gid >= 56:
            return (172, 220, 220, 230)
        return (98, 150, 72, 235)

    def _draw_radar_minimap(self, surface, player, enemies, boss) -> None:
        center = surface.get_width() // 2, surface.get_height() // 2
        radar_radius = surface.get_width() // 2 - 12
        world_radius = 900.0
        pygame.draw.circle(surface, (55, 72, 70, 210), center, radar_radius)
        pygame.draw.circle(surface, (125, 150, 140, 210), center, radar_radius, 1)

        def project(wx: float, wy: float) -> tuple[int, int]:
            dx = max(-world_radius, min(world_radius, wx - player.x))
            dy = max(-world_radius, min(world_radius, wy - player.y))
            return (
                center[0] + int(dx / world_radius * radar_radius),
                center[1] + int(dy / world_radius * radar_radius),
            )

        self._draw_minimap_entities(surface, player, enemies, boss, project)

    def _draw_minimap_entities(self, surface, player, enemies, boss, project) -> None:
        for enemy in enemies:
            if enemy.alive:
                pygame.draw.circle(surface, (230, 70, 65), project(enemy.x, enemy.y), 2)
        if boss and boss.alive:
            pygame.draw.circle(surface, (220, 60, 230), project(boss.x, boss.y), 4)
        px, py = project(player.x, player.y)
        pygame.draw.circle(surface, (80, 210, 255), (px, py), 4)
        pygame.draw.circle(surface, (245, 255, 255), (px, py), 4, 1)

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
                     offset_y: int, bar_w: int | None = None,
                     bar_h: int = 3, color=(205, 18, 62)) -> None:
        hp_ratio = entity.get_hp_ratio()
        if hp_ratio >= 1.0:
            return

        if bar_w is None:
            bar_w = max(self._zoom_len(24), int(offset_y * 1.35))

        bar_w = max(1, int(bar_w))
        bar_h = max(1, int(bar_h))
        bar_x = int(sx - bar_w / 2)
        bar_y = int(sy - offset_y)
        # Nền đỏ tối
        fill_w = int(round(bar_w * hp_ratio))
        pygame.draw.rect(self.screen, (70, 12, 28), (bar_x, bar_y + bar_h, bar_w, 1))
        pygame.draw.rect(self.screen, (75, 6, 22), (bar_x, bar_y, bar_w, bar_h))
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))

    def _spawn_leaf(self, x: float, y: float) -> None:
        import random as _rnd
        color_choices = [
            (76, 154, 42),     # Xanh lá tươi
            (56, 125, 34),     # Xanh lá đậm
            (102, 180, 64),    # Xanh lá mạ
            (145, 172, 58),    # Xanh lá vàng
            (205, 165, 45),    # Lá úa vàng
        ]
        color = _rnd.choice(color_choices)
        color = (
            max(0, min(255, color[0] + _rnd.randint(-12, 12))),
            max(0, min(255, color[1] + _rnd.randint(-12, 12))),
            max(0, min(255, color[2] + _rnd.randint(-8, 8))),
        )
        
        self.leaves.append({
            "x": x,
            "y": y,
            "vx": _rnd.uniform(-25.0, -5.0), # Gió nhẹ thổi sang bên trái
            "vy": _rnd.uniform(40.0, 65.0),  # Tốc độ rơi vừa phải
            "size_w": _rnd.uniform(5.0, 8.0),
            "size_h": _rnd.uniform(7.0, 11.0),
            "color": color,
            "angle": _rnd.uniform(0.0, 360.0),
            "rot_speed": _rnd.uniform(-80.0, 80.0),  # Tốc độ xoay chiếc lá
            "sway_speed": _rnd.uniform(2.5, 4.5),    # Tốc độ đung đưa
            "sway_amount": _rnd.uniform(20.0, 40.0), # Biên độ đung đưa
            "sway_phase": _rnd.uniform(0.0, math.tau),
            "life": _rnd.uniform(4.0, 6.0),
            "age": 0.0,
        })

    def _update_and_draw_leaves(self, dt: float, cam_x: float, cam_y: float) -> None:
        active_leaves = []
        for leaf in self.leaves:
            leaf["age"] += dt
            if leaf["age"] >= leaf["life"]:
                continue
            
            # Cập nhật chuyển động đung đưa hình sin
            sway = math.sin(leaf["age"] * leaf["sway_speed"] + leaf["sway_phase"]) * leaf["sway_amount"] * dt
            
            # Cập nhật vị trí world space
            leaf["x"] += leaf["vx"] * dt + sway * 2.0
            leaf["y"] += leaf["vy"] * dt
            leaf["angle"] += leaf["rot_speed"] * dt
            
            active_leaves.append(leaf)
            
            # Chuyển đổi sang vị trí màn hình
            sx, sy = self.world_to_screen(leaf["x"], leaf["y"], cam_x, cam_y)
            
            # Nếu lá nằm trong màn hình
            if -30 <= sx <= SCREEN_W + 30 and -30 <= sy <= SCREEN_H + 30:
                w = max(1, self._zoom_len(leaf["size_w"]))
                h = max(1, self._zoom_len(leaf["size_h"]))
                
                # Tạo surface cho chiếc lá
                leaf_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                
                # Vẽ hình chiếc lá hình thoi thuôn nhọn
                points = [
                    (w // 2, 0),
                    (w, h // 3),
                    (w // 2, h),
                    (0, h // 3),
                ]
                pygame.draw.polygon(leaf_surf, leaf["color"], points)
                
                # Xoay và vẽ lên màn hình
                rotated_surf = pygame.transform.rotate(leaf_surf, leaf["angle"])
                rect = rotated_surf.get_rect(center=(sx, sy))
                self.screen.blit(rotated_surf, rect)
                
        self.leaves = active_leaves
