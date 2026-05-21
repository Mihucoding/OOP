import math
from logic.entities.enemy import Enemy

class RangedEnemy(Enemy):
    """
    Quái tầm xa — giữ khoảng cách và bắn đạn.
    """
    STOP_DISTANCE = 350
    FIRE_RATE = 2.0  # giây giữa 2 lần bắn

    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.fire_timer = self.FIRE_RATE

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật status effects từ class cha
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.type == 'slow':
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        # 2. Logic di chuyển: Chỉ đuổi theo nếu ở xa
        dist = math.hypot(player_x - self.x, player_y - self.y)
        
        if dist > self.STOP_DISTANCE:
            move_x = player_x - self.x
            move_y = player_y - self.y
            if dist > 0:
                self.x += (move_x / dist) * self.speed * slow_factor * dt
                self.y += (move_y / dist) * self.speed * slow_factor * dt
        
        # 3. Cập nhật timer bắn
        if self.fire_timer > 0:
            self.fire_timer -= dt

    def can_fire(self) -> bool:
        return self.fire_timer <= 0 and self.cast_lock_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.FIRE_RATE
