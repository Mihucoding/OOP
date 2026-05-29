import math
from logic.entities.status_effect import StatusEffect


class Enemy:
    RADIUS    = 20
    BASE_HP   = 50
    BASE_SPEED = 80
    XP_VALUE  = 10

    def __init__(self, x: float, y: float, hp_mult=1.0, speed_mult=1.0):
        self.x       = float(x)
        self.y       = float(y)
        self.radius  = self.__class__.RADIUS
        self.max_hp  = self.__class__.BASE_HP * hp_mult
        self.hp      = float(self.max_hp)
        self.speed   = self.__class__.BASE_SPEED * speed_mult
        self.damage  = 20.0 * hp_mult
        self.xp_value = self.__class__.XP_VALUE
        self.alive   = True
        self.status_effects: list[StatusEffect] = []
        self.cast_lock_timer = 0.0

    def update(self, dt: float, player_x: float, player_y: float) -> None:
        # 1. Cập nhật status_effects và tính slow_factor tổng hợp
        slow_factor    = 1.0
        active_effects = []
        for eff in self.status_effects:
            eff.update(self, dt)
            if not eff.is_expired():
                active_effects.append(eff)
                # Mọi effect có slow_factor < 1.0 đều làm chậm (slow, chill, stun)
                if eff.slow_factor < 1.0:
                    slow_factor = min(slow_factor, eff.slow_factor)
        self.status_effects = active_effects
        if self.cast_lock_timer > 0:
            self.cast_lock_timer = max(0.0, self.cast_lock_timer - dt)
            return

        # 2. Di chuyển đuổi theo player
        move_x   = player_x - self.x
        move_y   = player_y - self.y
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            self.x += (move_x / move_len) * self.speed * slow_factor * dt
            self.y += (move_y / move_len) * self.speed * slow_factor * dt

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False

    def add_status(self, effect: StatusEffect) -> None:
        # Nếu đã có effect cùng loại → refresh remaining + tăng stacks (burn/chill)
        for eff in self.status_effects:
            if eff.type == effect.type:
                eff.remaining = max(eff.remaining, effect.remaining)
                if eff.type in ('burn', 'chill'):
                    eff.stacks = min(eff.stacks + 1, eff.max_stacks)
                return
        self.status_effects.append(effect)

    def drop_xp(self, lucky: float = 0.0) -> list:
        from logic.entities.xp_orb import scatter_xp
        # Lucky cao → thêm orb: 0→3, ≥20→4, ≥50→5
        count = 3 + (1 if lucky >= 20 else 0) + (1 if lucky >= 50 else 0)
        return scatter_xp(self.x, self.y, self.xp_value, count=count)

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp
