"""
StatusEffect — hiệu ứng trạng thái áp lên quái (burn, slow, poison).
"""


class StatusEffect:
    """
    Đại diện cho 1 hiệu ứng đang hoạt động trên quái.
    Được tạo bởi ElementRune khi đạn trúng.
    """

    def __init__(self, effect_type: str, damage_per_sec: float,
                 duration: float, slow_factor: float = 1.0):
        """
        effect_type    : 'burn' | 'poison' | 'slow'
        damage_per_sec : HP rút mỗi giây (0 nếu chỉ slow)
        duration       : tổng thời gian hiệu ứng (giây)
        slow_factor    : 1.0 = bình thường, 0.5 = chậm 50%
        """
        self.type = effect_type
        self.damage_per_sec = damage_per_sec
        self.duration = duration
        self.remaining = duration
        self.slow_factor = slow_factor

    def update(self, enemy, dt: float) -> None:
        """Cập nhật mỗi frame — giảm thời gian và gây damage nếu có."""
        self.remaining -= dt
        if self.damage_per_sec > 0:
            enemy.take_damage(self.damage_per_sec * dt)

    def is_expired(self) -> bool:
        return self.remaining <= 0
