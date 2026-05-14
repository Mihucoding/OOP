import math


class Player:
    RADIUS = 15
    BASE_HP = 100
    BASE_SPEED = 200       # pixel/giây
    BASE_FIRE_RATE = 0.5   # giây giữa 2 lần bắn
    BASE_DAMAGE = 20

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
        self.radius = Player.RADIUS
        self.max_hp = Player.BASE_HP
        self.hp = float(Player.BASE_HP)
        self.speed = Player.BASE_SPEED
        self.fire_rate = Player.BASE_FIRE_RATE
        self.damage = Player.BASE_DAMAGE
        self.alive = True
        self.fire_timer = 0.0   # đếm ngược, khi <= 0 mới được bắn

        # Rune Tree — import ở đây tránh circular import
        from logic.rune.rune_tree import RuneTree
        self.rune_tree = RuneTree()

        # Leveling
        self.level = 1
        self.xp = 0
        self.xp_to_next = 30   # XP cần lên cấp, tăng 1.4x mỗi cấp

    def update(self, dt: float, move_x: float, move_y: float) -> None:
        # move_x, move_y: từ input (-1, 0, 1)
        # 1. Normalize vector nếu (move_x, move_y) != (0, 0)
        # 2. self.x += direction.x * self.speed * dt
        # 3. self.y += direction.y * self.speed * dt
        # 4. Giảm fire_timer nếu > 0
        move_len = math.hypot(move_x, move_y)
        if move_len > 0:
            move_x /= move_len
            move_y /= move_len
        self.x += move_x * self.speed * dt
        self.y += move_y * self.speed * dt
        self.fire_timer = max(0.0, self.fire_timer - dt)

    def can_fire(self) -> bool:
        return self.fire_timer <= 0

    def reset_fire_timer(self) -> None:
        self.fire_timer = self.fire_rate

    def take_damage(self, amount: float) -> None:
        # Trừ HP, clamp về 0, set alive=False nếu hp<=0
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def add_xp(self, amount: int) -> bool:
        # Cộng XP, nếu đủ → level += 1, tính xp_to_next mới, trả về True
        # Công thức xp_to_next mới = int(xp_to_next * 1.4)
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.level += 1
            self.xp -= self.xp_to_next
            self.xp_to_next = int(self.xp_to_next * 1.4)
            leveled_up = True
        return leveled_up

    def get_hp_ratio(self) -> float:
        return self.hp / self.max_hp

    def get_xp_ratio(self) -> float:
        return self.xp / self.xp_to_next
