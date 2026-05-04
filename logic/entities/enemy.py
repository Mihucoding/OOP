import math
from logic.entities.status_effect import StatusEffect


class Enemy:
    RADIUS = 20
    BASE_HP = 50
    BASE_SPEED = 80
    XP_VALUE = 10

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.radius = Enemy.RADIUS
        self.max_hp = Enemy.BASE_HP
        self.hp = float(Enemy.BASE_HP)
        self.speed = Enemy.BASE_SPEED
        self.xp_value = Enemy.XP_VALUE
        self.alive = True
        self.status_effects: list[StatusEffect] = []

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật status_effects và tính slow_factor
        slow_factor = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                if eff.type == 'slow':
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        
        # 2. Logic di chuyển đuổi theo player
        move_x = player_x - self.x
        move_y = player_y - self.y
        move_len = math.hypot(move_x, move_y)
        
        if move_len > 0:
            self.x += (move_x / move_len) * self.speed * slow_factor * dt
            self.y += (move_y / move_len) * self.speed * slow_factor * dt

    def take_damage(self, amount: float) -> None:
        # Trừ HP, set alive=False nếu hp<=0
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def add_status(self, effect: StatusEffect) -> None:
        # Nếu đã có effect cùng loại → refresh remaining (lấy max)
        # Nếu chưa có → append vào list
        for eff in self.status_effects:
            if eff.type == effect.type:
                eff.remaining = max(eff.remaining, effect.remaining)
                return
        self.status_effects.append(effect)

    def drop_xp(self):
        # Import XPOrb ở đây để tránh circular import
        # Trả về XPOrb(self.x, self.y, self.xp_value)
        from logic.entities.xp_orb import XPOrb
        return XPOrb(self.x, self.y, self.xp_value)

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp
