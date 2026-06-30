"""
StatusEffect — hiệu ứng trạng thái áp lên quái (burn, chill, slow, stun, poison).
"""


class StatusEffect:
    """
    Đại diện cho 1 hiệu ứng đang hoạt động trên quái.
    Được tạo bởi ElementRune khi đạn trúng.
    """

    def __init__(self, effect_type: str, damage_per_sec: float,
                 duration: float, slow_factor: float = 1.0):
        """
        effect_type    : 'burn' | 'chill' | 'slow' | 'stun' | 'poison'
        damage_per_sec : HP rút mỗi giây (0 nếu chỉ slow/stun)
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

        elif self.damage_per_sec > 0:
            enemy.take_damage(self.damage_per_sec * dt)

    def is_expired(self) -> bool:
        return self.remaining <= 0
