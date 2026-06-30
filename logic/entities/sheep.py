import math
import random
from logic.entities.enemy import Enemy
from logic.entities.meat import Meat

class Sheep(Enemy):
    """
    Thực thể con cừu hòa bình.
    Kế thừa từ Enemy để tích hợp với hệ thống va chạm đạn/phép,
    nhưng không gây sát thương khi va chạm với player (damage = 0)
    và đi lang thang ngẫu nhiên thay vì đuổi theo player.
    """
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        self.max_hp = 10.0
        self.hp = 10.0
        self.speed = 35.0
        self.damage = 0.0
        self.xp_value = 0
        self.radius = 24.0  # Tăng bán kính va chạm lên 24.0 để khớp kích thước vẽ 80x80
        
        self.state = "idle"  # "idle", "wander", "eating"
        self.state_timer = random.uniform(2.0, 5.0)
        
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.facing_dir = 1

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        self.hurt_timer = max(0.0, getattr(self, 'hurt_timer', 0.0) - dt)
        if getattr(self, 'state', '') == 'die':
            self.die_timer = getattr(self, 'die_timer', 0.0) + dt
            if self.die_timer >= 0.05: # Cừu biến mất ngay lập tức
                self.alive = False
            return
            
        # 1. Cập nhật status effects tương tự Enemy
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects

        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        # 2. Xử lý máy trạng thái chuyển động lang thang của cừu
        self.state_timer -= dt
        if self.state_timer <= 0:
            self.state = random.choice(["idle", "wander", "eating"])
            self.state_timer = random.uniform(3.0, 6.0)
            if self.state == "wander":
                angle = random.uniform(0, math.tau)
                self.wander_dx = math.cos(angle)
                self.wander_dy = math.sin(angle)
                if self.wander_dx < 0:
                    self.facing_dir = -1
                elif self.wander_dx > 0:
                    self.facing_dir = 1
            else:
                self.wander_dx = 0.0
                self.wander_dy = 0.0

        # 3. Thực hiện di chuyển nếu đang wander
        if self.state == "wander":
            self.x += self.wander_dx * self.speed * slow_factor * dt
            self.y += self.wander_dy * self.speed * slow_factor * dt

    def drop_xp(self, lucky: float = 0.0) -> list:
        # Khi cừu chết, rơi ra đúng 1 Meat với vận tốc văng ngẫu nhiên
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 100)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        return [Meat(self.x, self.y, vx, vy)]
