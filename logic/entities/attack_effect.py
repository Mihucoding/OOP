"""
AttackEffect — các loại tấn công khác nhau ngoài Bullet thông thường.

Hệ thống:
  BloodBall    → dùng Bullet hiện tại (có visual_type='blood_ball')
  LightningBeam → tia sét tức thì theo đường thẳng
  IceEruption  → gai băng mọc từ đất tại vị trí target
  ImpactEffect → hiệu ứng nổ thuần visual, không gây damage
"""
import math
import random


# ── Proxy object cho rune_tree.on_hit ────────────────────────────────────────

class _HitProxy:
    """
    Giả lập Bullet để truyền vào rune_tree.on_hit.
    LightningBeam và IceEruption không phải Bullet nên cần proxy này.
    """
    def __init__(self, effect):
        self.element_stack   = 1
        self.bounce_count    = 0
        self.bounce_redirect = False
        self.alive           = True
        self.x               = effect.x
        self.y               = effect.y
        self.damage          = effect.damage
        angle = getattr(effect, 'angle_rad', 0.0)
        self.vx = math.cos(angle)
        self.vy = math.sin(angle)

    def redirect(self, new_vx: float, new_vy: float) -> None:
        pass   # beam/eruption không bị redirect


# ── LightningBeam ─────────────────────────────────────────────────────────────

class LightningBeam:
    """
    Tia sét tức thì: hit tất cả enemy trên đường thẳng từ player → target.
    Tồn tại ngắn (LIFETIME giây) chỉ để hiển thị visual.
    """

    LIFETIME    = 0.35    # giây hiển thị beam
    BEAM_LENGTH = 320     # pixel
    HIT_RADIUS  = 20      # bán kính va chạm quanh đường beam

    def __init__(self, x: float, y: float, angle_rad: float,
                 damage: float, rune_tree=None):
        self.x           = float(x)
        self.y           = float(y)
        self.angle_rad   = angle_rad
        self.damage      = damage
        self.rune_tree   = rune_tree
        self.alive       = True
        self.elapsed     = 0.0
        self.is_crit     = False
        self.visual_type = 'lightning_beam'
        self._hit_ids: set[int] = set()
        # BounceModifier chain
        self.chain_count = 0    # số lần đã chain
        self.max_chain   = 0    # giới hạn (được set từ BounceModifier.stack)

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.alive = False

    def get_end_point(self) -> tuple[float, float]:
        return (
            self.x + math.cos(self.angle_rad) * self.BEAM_LENGTH,
            self.y + math.sin(self.angle_rad) * self.BEAM_LENGTH,
        )

    def check_hits(self, enemies: list, boss) -> list:
        """
        Trả về list entity bị trúng lần đầu.
        Dùng phép chiếu điểm lên đoạn thẳng để tính khoảng cách.
        """
        ex, ey  = self.get_end_point()
        dx, dy  = ex - self.x, ey - self.y
        len_sq  = dx * dx + dy * dy
        if len_sq == 0:
            return []

        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)

        hits = []
        for entity in targets:
            if id(entity) in self._hit_ids:
                continue
            t  = max(0.0, min(1.0,
                    ((entity.x - self.x) * dx + (entity.y - self.y) * dy) / len_sq))
            cx = self.x + t * dx
            cy = self.y + t * dy
            if math.hypot(entity.x - cx, entity.y - cy) <= entity.radius + self.HIT_RADIUS:
                hits.append(entity)
                self._hit_ids.add(id(entity))
        return hits


# ── IceEruption ───────────────────────────────────────────────────────────────

class IceEruption:
    """
    Gai băng mọc từ đất tại vị trí target.
    Phase grow → active (gây AoE damage 1 lần) → fade.
    """

    GROW_DUR   = 0.30   # giây gai đang mọc (chưa damage)
    ACTIVE_DUR = 0.35   # giây gai đứng yên → gây damage
    FADE_DUR   = 0.40   # giây gai tan biến
    TOTAL_LIFE = GROW_DUR + ACTIVE_DUR + FADE_DUR

    AoE_RADIUS = 70     # bán kính gây sát thương

    def __init__(self, x: float, y: float, damage: float, rune_tree=None,
                 is_mini: bool = False):
        self.x           = float(x)
        self.y           = float(y)
        self.damage      = damage
        self.rune_tree   = rune_tree
        self.alive       = True
        self.elapsed     = 0.0
        self.is_crit     = False
        self.visual_type = 'ice_eruption'
        self._hit_ids: set[int]    = set()
        # BounceModifier: mini eruption tracking
        self.is_mini              = is_mini   # True → không spawn mini lại (tránh đệ quy)
        self._mini_spawned: set[int] = set()

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.TOTAL_LIFE:
            self.alive = False

    @property
    def phase(self) -> str:
        if self.elapsed < self.GROW_DUR:
            return 'grow'
        if self.elapsed < self.GROW_DUR + self.ACTIVE_DUR:
            return 'active'
        return 'fade'

    @property
    def anim_progress(self) -> float:
        """0.0→1.0 tiến trình animation toàn bộ vòng đời."""
        return min(1.0, self.elapsed / self.TOTAL_LIFE)

    def check_hits(self, enemies: list, boss) -> list:
        if self.phase != 'active':
            return []
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        hits = []
        for entity in targets:
            if id(entity) in self._hit_ids:
                continue
            if math.hypot(entity.x - self.x, entity.y - self.y) <= entity.radius + self.AoE_RADIUS:
                hits.append(entity)
                self._hit_ids.add(id(entity))
        return hits


# ── AoEBurst — skill AoE tổng quát ───────────────────────────────────────────

class AoEBurst:
    """
    AoE tại điểm cố định, dùng cho các skill (BloodBomb, ThunderStrike…).
    Lifecycle giống IceEruption nhưng visual_type và radius tuỳ chỉnh.
    """

    GROW_DUR   = 0.15
    ACTIVE_DUR = 0.30
    FADE_DUR   = 0.35

    def __init__(self, x: float, y: float, damage: float, radius: float,
                 visual_type: str = 'blood_impact',
                 rune_tree=None, life_scale: float = 1.0):
        self.x           = float(x)
        self.y           = float(y)
        self.damage      = damage
        self.AoE_RADIUS  = radius
        self.visual_type = visual_type
        self.rune_tree   = rune_tree
        self.alive       = True
        self.elapsed     = 0.0
        self.is_crit     = False
        self._hit_ids: set[int] = set()
        # life_scale > 1.0 → toàn bộ hiệu ứng chậm lại (ultimate "nặng" hơn)
        self.GROW_DUR    = self.GROW_DUR   * life_scale
        self.ACTIVE_DUR  = self.ACTIVE_DUR * life_scale
        self.FADE_DUR    = self.FADE_DUR   * life_scale
        self.TOTAL_LIFE  = self.GROW_DUR + self.ACTIVE_DUR + self.FADE_DUR

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.TOTAL_LIFE:
            self.alive = False

    @property
    def phase(self) -> str:
        if self.elapsed < self.GROW_DUR:
            return 'grow'
        if self.elapsed < self.GROW_DUR + self.ACTIVE_DUR:
            return 'active'
        return 'fade'

    @property
    def anim_progress(self) -> float:
        return min(1.0, self.elapsed / self.TOTAL_LIFE)

    def check_hits(self, enemies: list, boss) -> list:
        if self.phase != 'active':
            return []
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        hits = []
        for entity in targets:
            if id(entity) in self._hit_ids:
                continue
            if math.hypot(entity.x - self.x, entity.y - self.y) <= entity.radius + self.AoE_RADIUS:
                hits.append(entity)
                self._hit_ids.add(id(entity))
        return hits


# ── VortexZone — lốc xoáy đứng yên, hút quái về tâm (Perfect Storm) ──────────

class VortexZone:
    """
    Vùng lốc xoáy trong `duration` giây — TRÔI CHẬM về phía trước theo hướng
    đường đạn đã cast ra nó, vừa đi vừa lượn zigzag ngang nhẹ (không đứng yên
    1 chỗ, cũng không chỉ dao động qua lại tại điểm cast).
    - Gây damage 1 lần cho quái mới vào vùng (giống AoEBurst).
    - Mỗi frame còn hoạt động, hút MỌI quái đang đứng trong vùng về tâm HIỆN
      TẠI (áp/refresh StatusEffect 'vortex' — mạnh dần theo `vortex_stacks`).
    Dùng cho PerfectStormModifier (Trigger "Triggered on spawn").
    """

    GROW_DUR = 0.2   # chỉ để hiệu ứng hiện dần, không ảnh hưởng damage/hút

    DRIFT_SPEED      = 40.0   # px/s — tốc độ trôi tới theo hướng đường đạn
    ZIGZAG_AMPLITUDE = 22.0   # px — biên độ lượn ngang quanh trục trôi
    ZIGZAG_SPEED     = 2.4    # rad/s — tần số lượn ngang
    WOBBLE_JITTER    = 0.8    # rad/s — tốc độ đổi độ lệch ngẫu nhiên (random walk)
    WOBBLE_LIMIT     = 0.6    # kẹp biên độ lệch ngẫu nhiên (tỉ lệ ZIGZAG_AMPLITUDE)

    def __init__(self, x: float, y: float, damage: float, radius: float,
                 duration: float, vortex_stacks: int,
                 pull_strength: float = 90.0,
                 visual_type: str = 'wind_vortex', rune_tree=None,
                 dir_x: float = 0.0, dir_y: float = 0.0):
        self.origin_x      = float(x)
        self.origin_y      = float(y)
        self.x             = float(x)
        self.y             = float(y)
        self.damage        = damage
        self.AoE_RADIUS    = radius
        self.duration      = duration
        self.vortex_stacks = vortex_stacks
        self.pull_strength = pull_strength
        self.visual_type   = visual_type
        self.rune_tree     = rune_tree
        self.alive         = True
        self.elapsed       = 0.0
        self.is_crit       = False
        self._hit_ids: set[int] = set()
        # Hướng trôi: theo hướng đường đạn nếu có, không thì random (Ice/Lightning
        # không có khái niệm "đường đạn" nên fallback hướng ngẫu nhiên).
        self._travel_angle = (math.atan2(dir_y, dir_x) if (dir_x or dir_y)
                              else random.uniform(0.0, math.tau))
        self._zigzag_phase = random.uniform(0.0, math.tau)   # lệch pha lượn ngẫu nhiên
        self._wobble        = 0.0   # độ lệch ngang ngẫu nhiên cộng dồn nhẹ (random walk)

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.alive = False
            return
        # Trôi chậm về phía trước theo hướng đường đạn.
        self.origin_x += math.cos(self._travel_angle) * self.DRIFT_SPEED * dt
        self.origin_y += math.sin(self._travel_angle) * self.DRIFT_SPEED * dt

        # Random walk nhẹ trên độ lệch ngang -> zigzag không đều tăm tắp.
        self._wobble += random.uniform(-self.WOBBLE_JITTER, self.WOBBLE_JITTER) * dt
        limit = self.WOBBLE_LIMIT
        self._wobble = max(-limit, min(limit, self._wobble))

        # Lượn zigzag vuông góc hướng trôi, cộng thêm độ lệch ngẫu nhiên.
        perp = self._travel_angle + math.pi / 2
        lateral = math.sin(self.elapsed * self.ZIGZAG_SPEED + self._zigzag_phase)
        lateral = (lateral + self._wobble) * self.ZIGZAG_AMPLITUDE
        self.x = self.origin_x + math.cos(perp) * lateral
        self.y = self.origin_y + math.sin(perp) * lateral

    @property
    def phase(self) -> str:
        return 'grow' if self.elapsed < self.GROW_DUR else 'active'

    @property
    def anim_progress(self) -> float:
        return min(1.0, self.elapsed / max(0.001, self.duration))

    def check_hits(self, enemies: list, boss) -> list:
        """Damage 1 lần lúc quái mới bước vào vùng — dùng chung interface AoE."""
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        hits = []
        for entity in targets:
            if id(entity) in self._hit_ids:
                continue
            if math.hypot(entity.x - self.x, entity.y - self.y) <= entity.radius + self.AoE_RADIUS:
                hits.append(entity)
                self._hit_ids.add(id(entity))
        return hits

    def apply_pull(self, enemies: list, boss) -> None:
        """Gọi mỗi frame — hút MỌI quái đang trong vùng về tâm (kể cả đã bị
        damage rồi), tách biệt khỏi check_hits (chỉ bắn 1 lần)."""
        from logic.entities.status_effect import StatusEffect
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        for entity in targets:
            if math.hypot(entity.x - self.x, entity.y - self.y) <= self.AoE_RADIUS:
                vortex              = StatusEffect('vortex', 0.0, duration=0.3)
                vortex.center_x     = self.x
                vortex.center_y     = self.y
                vortex.pull_strength = self.pull_strength
                vortex.stacks       = self.vortex_stacks
                entity.add_status(vortex)


# ── ImpactEffect (visual only) ────────────────────────────────────────────────

class ImpactEffect:
    """Hiệu ứng nổ thuần visual (không gây damage)."""

    def __init__(self, x: float, y: float,
                 visual_type: str = 'blood_impact',
                 lifetime: float = 0.55):
        self.x           = float(x)
        self.y           = float(y)
        self.alive       = True
        self.elapsed     = 0.0
        self.LIFETIME    = lifetime
        self.visual_type = visual_type
        self.damage      = 0.0
        self.rune_tree   = None
        self.is_crit     = False

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.alive = False

    def check_hits(self, enemies, boss) -> list:
        return []


# ── FireBreathEffect — đạn lửa stream (giữ RMB) ───────────────────────────────

class FireBreathEffect:
    """
    1 luồng lửa ngắn bay về hướng chuột — xuyên nhiều enemy.
    Spawn liên tục khi giữ RMB (game_loop điều khiển nhịp spawn).
    """

    SPEED    = 520.0
    LIFETIME = 0.35    # bay ngắn → cảm giác phun gần
    HIT_RADIUS = 26

    def __init__(self, x: float, y: float, angle_rad: float,
                 damage: float, rune_tree=None):
        self.x           = float(x)
        self.y           = float(y)
        self.angle_rad   = angle_rad
        self.vx          = math.cos(angle_rad) * self.SPEED
        self.vy          = math.sin(angle_rad) * self.SPEED
        self.damage      = damage
        self.rune_tree   = rune_tree
        self.alive       = True
        self.elapsed     = 0.0
        self.is_crit     = False
        self.visual_type = 'fire_breath'
        self._hit_ids: set[int] = set()

    def update(self, dt: float) -> None:
        self.x       += self.vx * dt
        self.y       += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.alive = False

    def check_hits(self, enemies: list, boss) -> list:
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        hits = []
        for e in targets:
            if id(e) in self._hit_ids:
                continue
            if math.hypot(e.x - self.x, e.y - self.y) <= e.radius + self.HIT_RADIUS:
                hits.append(e)
                self._hit_ids.add(id(e))
        return hits


# ── FireBreathJet — 1 luồng lửa liền (giữ RMB) ────────────────────────────────

class FireBreathJet:
    """
    MỘT luồng lửa duy nhất gắn vào player, hướng về chuột.
    Gây damage theo hình nón (cone) liên tục theo nhịp TICK.
    game_loop điều khiển vòng đời (aim mỗi frame, set alive=False khi ngừng).
    """

    LENGTH     = 340.0          # tầm xa tối đa của luồng lửa (kéo dài)
    HALF_ANGLE = math.radians(18)
    TICK       = 0.12           # nhịp gây damage cho mỗi enemy
    visual_type = 'fire_breath_jet'

    def __init__(self, x: float, y: float, angle_rad: float,
                 damage: float, rune_tree=None):
        self.x          = float(x)
        self.y          = float(y)
        self.angle_rad  = angle_rad
        self.damage     = damage
        self.rune_tree  = rune_tree
        self.alive      = True
        self.elapsed    = 0.0
        self.is_crit    = False
        self._tick      = 0.0
        self._hit_ids: set[int] = set()

    def aim(self, x: float, y: float, angle_rad: float, damage: float) -> None:
        """Cập nhật gốc + hướng + damage mỗi frame (theo player & chuột)."""
        self.x         = float(x)
        self.y         = float(y)
        self.angle_rad = angle_rad
        self.damage    = damage

    @property
    def ramp(self) -> float:
        """0→1: luồng lửa vươn dài nhanh khi mới bắt đầu."""
        return min(1.0, self.elapsed / 0.15)

    @property
    def length(self) -> float:
        return self.LENGTH * self.ramp

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self._tick   -= dt
        if self._tick <= 0.0:
            self._tick = self.TICK
            self._hit_ids.clear()   # cho phép gây damage lại theo nhịp

    def check_hits(self, enemies: list, boss) -> list:
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        reach = self.length
        hits  = []
        for e in targets:
            if id(e) in self._hit_ids:
                continue
            dx, dy = e.x - self.x, e.y - self.y
            dist   = math.hypot(dx, dy)
            if dist > reach + e.radius or dist == 0:
                continue
            # Góc lệch so với hướng luồng lửa
            ang_to = math.atan2(dy, dx)
            diff   = abs((ang_to - self.angle_rad + math.pi) % (2 * math.pi) - math.pi)
            if diff <= self.HALF_ANGLE:
                hits.append(e)
                self._hit_ids.add(id(e))
        return hits


# ── AirBurstEffect — luồng gió charged (giữ LMB) ──────────────────────────────

class AirBurstEffect:
    """
    Luồng gió bay thẳng, xuyên enemy và đẩy lùi (knockback).
    Độ dài/knockback phụ thuộc charge_ratio (0..1) lúc tạo.
    """

    BASE_SPEED = 560.0

    def __init__(self, x: float, y: float, angle_rad: float,
                 damage: float, charge_ratio: float, rune_tree=None):
        self.x            = float(x)
        self.y            = float(y)
        self.angle_rad    = angle_rad
        self.charge_ratio = max(0.0, min(1.0, charge_ratio))
        self.vx           = math.cos(angle_rad) * self.BASE_SPEED
        self.vy           = math.sin(angle_rad) * self.BASE_SPEED
        self.damage       = damage
        self.rune_tree    = rune_tree
        self.alive        = True
        self.elapsed      = 0.0
        self.is_crit      = False
        self.visual_type  = 'air_burst'
        # Charge cao → bay xa hơn + knockback mạnh + hitbox lớn
        self.lifetime     = 0.30 + self.charge_ratio * 0.55     # 0.30..0.85s
        self.knockback    = 150.0 + self.charge_ratio * 250.0   # 150..400px
        self.hit_radius   = 28 + self.charge_ratio * 30         # 28..58
        self.apply_stun   = self.charge_ratio >= 0.85
        self._hit_ids: set[int] = set()

    def update(self, dt: float) -> None:
        self.x       += self.vx * dt
        self.y       += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= self.lifetime:
            self.alive = False

    def check_hits(self, enemies: list, boss) -> list:
        targets = [e for e in enemies if e.alive]
        if boss and boss.alive:
            targets.append(boss)
        hits = []
        for e in targets:
            if id(e) in self._hit_ids:
                continue
            if math.hypot(e.x - self.x, e.y - self.y) <= e.radius + self.hit_radius:
                hits.append(e)
                self._hit_ids.add(id(e))
        return hits
