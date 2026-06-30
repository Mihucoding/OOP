"""
VFXManager — tải sprite sheet, tạo SpriteAnimator cho từng loại đạn.

Chỉ được import trong ui/ (dùng pygame).
logic/ không import file này.
"""
import os
import pygame

# ── Đường dẫn base ────────────────────────────────────────────────────────────
_HERE   = os.path.dirname(__file__)
_ASSETS = os.path.normpath(os.path.join(_HERE, '..', 'assets', 'sprites'))
_BLOOD  = os.path.join(_ASSETS, 'Pixel Art VFX - Blood Mage - FREE Version')
_LIGHT  = os.path.join(_ASSETS, 'Pixel Art Skill Animations - Lightning')
_FROST  = os.path.join(_ASSETS, 'Pixel Art VFX - Frost Knight - FREE Version')
_FIRE1  = os.path.join(_ASSETS, 'Fire Effect 1', 'Fire Effect 1')
_FIRE2  = os.path.join(_ASSETS, 'Fire Effect 2', 'Fire Effect 2')
_WIND   = os.path.join(_ASSETS, 'Wind Effect 02', 'Wind Effect 02')

# ── Thông số sprite sheet ─────────────────────────────────────────────────────
# key → (path, frame_w, frame_h, frame_count, cols_per_row, fps, loop)
VFX_SPECS: dict[str, tuple] = {
    # Blood orb đang bay (4 frames, 1 hàng ngang)
    'blood_fly': (
        os.path.join(_BLOOD, 'VFX3', 'sprite-sheet.png'),
        128, 128, 4, 4, 10, True,
    ),
    # Vụ nổ khi blood trúng (12 frames, 1 hàng ngang)
    'blood_impact': (
        os.path.join(_BLOOD, 'VFX2', 'sprite-sheet.png'),
        128, 128, 12, 12, 18, False,
    ),
    # Lightning beam ngang → sẽ rotate (4 frames, 1 hàng ngang)
    'lightning_beam': (
        os.path.join(_LIGHT, 'VFX1', 'Sprite-sheet', 'Sprite-sheet.png'),
        256, 128, 4, 4, 16, False,
    ),
    # Lightning sét đánh xuống (5 frames, 1 hàng ngang)
    'lightning_strike': (
        os.path.join(_LIGHT, 'VFX3', 'Sprite-sheet', 'Sprite-sheet.png'),
        128, 256, 5, 5, 16, False,
    ),
    # Ice eruption từ đất (11 frames, 5 frame/hàng, 3 hàng)
    'ice_eruption': (
        os.path.join(_FROST, 'VFX3', 'sprite-sheet', 'sprite-sheet.png'),
        256, 128, 11, 5, 16, False,
    ),

    # ── Fire Effect 1 ─────────────────────────────────────────────────────────
    # FireBolt bay (4 frame đầu sạch, loop mượt) — sheet 528×48, 11 frame
    'fire_bolt': (
        os.path.join(_FIRE1, 'Firebolt SpriteSheet.png'),
        48, 48, 4, 11, 11, True,
    ),
    # FireBolt impact khi trúng — sheet 240×48, 5 frame
    'fire_bolt_hit': (
        os.path.join(_FIRE1, 'Fire Breath hit effect SpriteSheet.png'),
        48, 48, 5, 5, 18, False,
    ),
    # Fire Breath cone (stream) — sheet 384×144, 4 cột × 3 hàng = 12 frame
    'fire_breath': (
        os.path.join(_FIRE1, 'Fire Breath SpriteSheet.png'),
        96, 48, 12, 4, 22, True,
    ),

    # ── Fire Effect 2 ─────────────────────────────────────────────────────────
    # Fire Explosion lớn (double-tap) — sheet 864×48, 18 frame 1 hàng
    # fps chậm hơn → vụ nổ "nặng" hơn (khớp life_scale 1.6 ở game_loop)
    'fire_explosion': (
        os.path.join(_FIRE2, 'Explosion 2 SpriteSheet.png'),
        48, 48, 18, 18, 15, False,
    ),

    # ── Wind Effect 02 ────────────────────────────────────────────────────────
    # Air Burst (charged left-click) — sheet 144×144, 3×3 = 9 frame, rotate
    'air_burst': (
        os.path.join(_WIND, 'Air Burst.png'),
        48, 48, 9, 3, 18, False,
    ),
    # Air Explosion (ultimate) — sheet 128×96, 4×3 = 12 frame
    # fps chậm hơn → khớp life_scale 1.5 ở game_loop
    'air_explosion': (
        os.path.join(_WIND, 'Air Explosion.png'),
        32, 32, 12, 4, 11, False,
    ),
}

# Kích thước hiển thị trên màn (scale để phù hợp game 1280×720)
VFX_DISPLAY_SIZE: dict[str, tuple[int, int]] = {
    'blood_fly':       (48,  48),
    'blood_impact':    (80,  80),
    'lightning_beam':  (320, 64),   # kéo dài theo chiều beam
    'lightning_strike':(64, 128),
    'ice_eruption':    (160, 80),
    'fire_bolt':       (44,  44),
    'fire_bolt_hit':   (56,  56),
    'fire_breath':     (130, 65),   # cone, rotate theo hướng
    'fire_explosion':  (200, 200),
    'air_burst':       (110, 110),  # rotate theo hướng
    'air_explosion':   (240, 240),  # scale lớn từ 32px source
}


# ── SpriteAnimator ────────────────────────────────────────────────────────────

class SpriteAnimator:
    """Quản lý một animation từ sprite sheet đã slice."""

    def __init__(self, sheet: pygame.Surface, frame_w: int, frame_h: int,
                 frame_count: int, cols: int, fps: float, loop: bool):
        self.frame_w     = frame_w
        self.frame_h     = frame_h
        self.fps         = fps
        self.loop        = loop
        self._elapsed    = 0.0
        self._done       = False
        self.frames: list[pygame.Surface] = []

        for i in range(frame_count):
            row  = i // cols
            col  = i % cols
            rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
            surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), rect)
            self.frames.append(surf)

    # ── Cập nhật timer ────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._elapsed += dt
        total = len(self.frames) / self.fps
        if not self.loop and self._elapsed >= total:
            self._elapsed = total - 1e-9
            self._done    = True
        elif self.loop:
            self._elapsed %= total

    def current_frame(self) -> pygame.Surface:
        idx = min(int(self._elapsed * self.fps), len(self.frames) - 1)
        return self.frames[idx]

    def is_done(self) -> bool:
        return self._done

    # ── Clone (reset timer, dùng chung frames) ────────────────────────────────

    def clone(self) -> 'SpriteAnimator':
        obj              = object.__new__(SpriteAnimator)
        obj.frame_w      = self.frame_w
        obj.frame_h      = self.frame_h
        obj.fps          = self.fps
        obj.loop         = self.loop
        obj._elapsed     = 0.0
        obj._done        = False
        obj.frames       = self.frames   # read-only share
        return obj


# ── VFXLibrary (singleton) ────────────────────────────────────────────────────

class VFXLibrary:
    """
    Tải và cache SpriteAnimator template cho mỗi loại VFX.
    Gọi load_all() một lần khi khởi tạo game.
    Sau đó dùng spawn(key) để lấy animator mới cho từng effect.
    """

    def __init__(self):
        self._templates: dict[str, SpriteAnimator] = {}
        self._loaded = False

    def load_all(self) -> None:
        if self._loaded:
            return
        for key, (path, fw, fh, count, cols, fps, loop) in VFX_SPECS.items():
            try:
                # Tải raw rồi convert riêng để tránh exception chain bị treo
                raw   = pygame.image.load(path)
                sheet = raw.convert_alpha()
                self._templates[key] = SpriteAnimator(sheet, fw, fh, count, cols, fps, loop)
            except Exception as e:
                print(f'[VFX] Không tải được "{key}": {e}')
            finally:
                # Xoá bất kỳ SDL error state nào do libpng iCCP warnings để lại
                pygame.get_error()
        self._loaded = True

    def spawn(self, key: str) -> SpriteAnimator | None:
        """Trả về animator độc lập (clone) để gắn vào 1 effect."""
        tmpl = self._templates.get(key)
        return tmpl.clone() if tmpl else None

    def has(self, key: str) -> bool:
        return key in self._templates


# ── Global instance ───────────────────────────────────────────────────────────

vfx_lib = VFXLibrary()   # load_all() gọi trong GameLoop.__init__


# ── AnimatorPool: theo dõi animator per effect ───────────────────────────────

class AnimatorPool:
    """
    Gắn SpriteAnimator vào từng effect (theo id).
    Gọi update() mỗi frame, get() để lấy frame hiện tại.
    Tự dọn dẹp khi effect chết.
    """

    # visual_type → VFX key cho SpriteAnimator
    _KEY_MAP = {
        'blood_ball':      'blood_fly',
        'blood_impact':    'blood_impact',
        'lightning_beam':  'lightning_beam',
        'lightning_strike':'lightning_strike',
        'ice_eruption':    'ice_eruption',
        'fire_bolt':       'fire_bolt',
        'fire_bolt_hit':   'fire_bolt_hit',
        'fire_breath':     'fire_breath',
        'fire_breath_jet': 'fire_breath',
        'fire_explosion':  'fire_explosion',
        'air_burst':       'air_burst',
        'air_explosion':   'air_explosion',
    }

    def __init__(self):
        self._pool: dict[int, SpriteAnimator] = {}

    def update_and_get(self, effect, dt: float) -> SpriteAnimator | None:
        """Cập nhật animator của effect và trả về animator."""
        eid = id(effect)
        if eid not in self._pool:
            key  = self._KEY_MAP.get(getattr(effect, 'visual_type', ''))
            anim = vfx_lib.spawn(key) if key else None
            if anim is None:
                return None
            self._pool[eid] = anim
        anim = self._pool[eid]
        anim.update(dt)
        return anim

    def cleanup(self, live_ids: set[int]) -> None:
        """Xoá animator của các effect đã chết."""
        dead = [k for k in self._pool if k not in live_ids]
        for k in dead:
            del self._pool[k]
