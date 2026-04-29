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
        # 1. Cập nhật và dọn status_effects hết hạn
        # 2. Tính slow_factor tổng hợp từ các effect loại 'slow'
        #    (lấy giá trị nhỏ nhất, mặc định 1.0)
        # 3. Tính hướng đến player (normalize), di chuyển với speed * slow_factor
        pass

    def take_damage(self, amount: float) -> None:
        # Trừ HP, set alive=False nếu hp<=0
        pass

    def add_status(self, effect: StatusEffect) -> None:
        # Nếu đã có effect cùng loại → refresh remaining (lấy max)
        # Nếu chưa có → append vào list
        pass

    def drop_xp(self):
        # Import XPOrb ở đây để tránh circular import
        # Trả về XPOrb(self.x, self.y, self.xp_value)
        pass

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp
