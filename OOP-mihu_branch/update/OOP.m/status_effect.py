# status_effect.py
"""
StatusEffect — hiệu ứng trạng thái áp lên quái (burn, slow, poison).
"""

class StatusEffect:
    """
    Đại diện cho 1 hiệu ứng đang hoạt động trên quái.
    """

    def __init__(self, effect_type: str, damage_per_sec: float,
                 duration: float, slow_factor: float = 1.0):
        self.type = effect_type
        self.damage_per_sec = damage_per_sec
        self.duration = duration
        self.remaining = duration
        self.base_slow_factor = slow_factor # Rename to avoid confusion with dynamic slow
        self.slow_factor = slow_factor
        self.stacks = 1
        self.max_stacks = 5

    def update(self, enemy, dt: float) -> None:
        """Cập nhật mỗi frame — giảm thời gian và gây damage nếu có."""
        self.remaining -= dt
        
        # Stacking logic
        if self.type == 'burn':
            if self.stacks >= 5:
                enemy.take_damage(enemy.max_hp * 0.05 * dt)
            elif self.damage_per_sec > 0:
                enemy.take_damage(self.damage_per_sec * dt)
        elif self.type == 'chill':
            # 5 stacks = frozen (slow_factor 0)
            # Each stack adds more slow
            self.slow_factor = max(0.0, 1.0 - (self.stacks / 5.0))
            if self.damage_per_sec > 0:
                enemy.take_damage(self.damage_per_sec * dt)
        elif self.damage_per_sec > 0:
            enemy.take_damage(self.damage_per_sec * dt)

    def is_expired(self) -> bool:
        return self.remaining <= 0
