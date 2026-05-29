import math
from logic.entities.enemy import Enemy

class RangedEnemy(Enemy):
    """
    Quái tầm xa — giữ khoảng cách và bắn đạn.
    """
    STOP_DISTANCE = 350
    FIRE_RATE = 2.0  # giây giữa 2 lần bắn

    def __init__(self, x: float, y: float, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, hp_mult, speed_mult)
        self.fire_timer = self.FIRE_RATE

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        self.hurt_timer = max(0.0, getattr(self, 'hurt_timer', 0.0) - dt)
        if getattr(self, 'state', '') == 'die':
            self.die_timer += dt
            if self.die_timer >= 1.2:
                self.alive = False
            return
            
        # 1. Cập nhật status effects từ class cha
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        
        # Quay mặt theo hướng player bất kể có đang di chuyển hay không
        move_x = player_x - self.x
        if move_x != 0:
            self.facing_dir = 1 if move_x > 0 else -1
            
        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        # 2. Logic di chuyển: Chỉ đuổi theo nếu ở xa
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist > self.STOP_DISTANCE:
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
        self.cast_lock_timer = 0.5  # Dừng lại 0.5s khi bắn
