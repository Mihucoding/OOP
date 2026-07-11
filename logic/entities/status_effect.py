"""
StatusEffect — hiệu ứng trạng thái áp lên quái (burn, chill, slow, stun, poison, vortex).
"""
import math


class StatusEffect:
    """
    Đại diện cho 1 hiệu ứng đang hoạt động trên quái.
    Được tạo bởi ElementRune khi đạn trúng.
    """

    def __init__(self, effect_type: str, damage_per_sec: float,
                 duration: float, slow_factor: float = 1.0):
        """
        effect_type    : 'burn' | 'chill' | 'slow' | 'stun' | 'poison' | 'vortex'
        damage_per_sec : HP rút mỗi giây (0 nếu chỉ slow/stun/vortex)
        duration       : tổng thời gian hiệu ứng (giây)
        slow_factor    : 1.0 = bình thường, 0.0 = đứng yên hoàn toàn
        """
        self.type           = effect_type
        self.damage_per_sec = damage_per_sec
        self.duration       = duration
        self.remaining      = duration
        self.slow_factor    = slow_factor
        self.stacks         = 1
        self.max_stacks     = 5
        # Chỉ dùng cho 'vortex' — tâm hút + tốc độ hút (set bởi VortexZone)
        self.center_x        = 0.0
        self.center_y        = 0.0
        self.pull_strength   = 0.0

    def update(self, enemy, dt: float) -> None:
        """Cập nhật mỗi frame — giảm thời gian và gây damage nếu có."""
        self.remaining -= dt

        if self.type == 'burn':
            # 5 stacks: thiêu đốt 5% max HP/s
            if self.stacks >= self.max_stacks:
                enemy.take_damage(enemy.max_hp * 0.05 * dt)
            elif self.damage_per_sec > 0:
                enemy.take_damage(self.damage_per_sec * dt)

        elif self.type == 'chill':
            # Mỗi stack giảm tốc thêm 20% (5 stacks = đóng băng hoàn toàn)
            self.slow_factor = max(0.0, 1.0 - (self.stacks / 5.0))
            if self.damage_per_sec > 0:
                enemy.take_damage(self.damage_per_sec * dt)

        elif self.type == 'vortex':
            # Hút quái về tâm cơn lốc — mạnh dần theo số stack (VD Perfect Storm)
            dx, dy = self.center_x - enemy.x, self.center_y - enemy.y
            dist   = math.hypot(dx, dy)
            if dist > 1.0:
                pull = self.pull_strength * self.stacks * dt
                enemy.x += (dx / dist) * pull
                enemy.y += (dy / dist) * pull

        elif self.damage_per_sec > 0:
            enemy.take_damage(self.damage_per_sec * dt)

    def is_expired(self) -> bool:
        return self.remaining <= 0
