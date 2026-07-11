"""
5 Ultimate cụ thể — mỗi class chỉ override name/color/_apply (AoE quanh
player, chọn qua get_ultimate_for_spell() theo Element ở Slot 0). Gộp vào 1
file vì mỗi class quá nhỏ (17-33 dòng) và cùng 1 khuôn (Strategy Pattern kế
thừa UltimateAbility) — trước đây tách riêng fire_nova.py/ice_blizzard.py/
lightning_storm.py/wind_cyclone.py/shadow_nova.py.
"""
import math
from logic.abilities.ultimate.ultimate_base import UltimateAbility
from logic.entities.status_effect import StatusEffect


class FireNova(UltimateAbility):
    """Vòng lửa nổ bán kính 220px — burn tất cả + đẩy ra ngoài."""
    COOLDOWN  = 8.0
    RADIUS    = 220.0
    DAMAGE    = 40.0
    PUSHBACK  = 160.0   # px knockback

    @property
    def name(self): return "Fire Nova"
    @property
    def color(self): return (255, 100, 20)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            e.add_status(StatusEffect('burn', damage_per_sec=12.0, duration=4.0))
            # Đẩy ra xa tâm player
            dx = e.x - player.x
            dy = e.y - player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                e.x += (dx / dist) * self.PUSHBACK
                e.y += (dy / dist) * self.PUSHBACK


class IceBlizzard(UltimateAbility):
    """Bão băng bán kính 240px — đóng băng + damage tất cả enemy."""
    COOLDOWN = 9.0
    RADIUS   = 240.0
    DAMAGE   = 25.0
    FREEZE_DURATION = 3.0

    @property
    def name(self): return "Ice Blizzard"
    @property
    def color(self): return (140, 200, 255)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            # Stun = đóng băng hoàn toàn
            e.add_status(StatusEffect(
                'stun', 0.0, self.FREEZE_DURATION, slow_factor=0.0))
            e.add_status(StatusEffect(
                'chill', 0.0, self.FREEZE_DURATION, slow_factor=0.0))


class LightningStorm(UltimateAbility):
    """Sét dây chuyền — stun + 60 damage tối đa 6 enemy."""
    COOLDOWN     = 7.0
    RADIUS       = 200.0
    DAMAGE       = 60.0
    MAX_TARGETS  = 6
    STUN_DUR     = 1.2

    @property
    def name(self): return "Thunder Chain"
    @property
    def color(self): return (200, 180, 255)

    def _apply(self, player, targets, context):
        hit = targets[:self.MAX_TARGETS]
        for e in hit:
            e.take_damage(self.DAMAGE)
            e.cast_lock_timer = max(getattr(e, 'cast_lock_timer', 0.0), self.STUN_DUR)
            context.get('effects', []).append({
                'kind': 'lightning_ultimate',
                'x': e.x,
                'y': e.y,
                'duration': 0.35,
            })


class WindCyclone(UltimateAbility):
    """Lốc xoáy — hút enemy vào tâm rồi knockback ra ngoài mạnh."""
    COOLDOWN   = 8.0
    RADIUS     = 250.0
    DAMAGE     = 30.0
    PULL_DIST  = 80.0    # hút vào
    PUSH_DIST  = 220.0   # đẩy ra

    @property
    def name(self): return "Wind Cyclone"
    @property
    def color(self): return (160, 230, 160)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            dx = e.x - player.x
            dy = e.y - player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                nx, ny = dx / dist, dy / dist
                # Hút vào trước
                e.x = player.x + nx * max(0, dist - self.PULL_DIST)
                e.y = player.y + ny * max(0, dist - self.PULL_DIST)
                # Rồi đẩy ra
                e.x += nx * self.PUSH_DIST
                e.y += ny * self.PUSH_DIST
            e.add_status(StatusEffect('slow', 0.0, 3.0, slow_factor=0.4))


class ShadowNova(UltimateAbility):
    """Nova bóng tối — AoE damage thuần, không cần element (fallback khi
    Slot 0 chưa có/không khớp Fire/Ice/Lightning/Wind)."""
    COOLDOWN = 8.0
    RADIUS   = 180.0
    DAMAGE   = 50.0

    @property
    def name(self): return "Shadow Nova"
    @property
    def color(self): return (160, 80, 200)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
