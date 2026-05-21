import math


class Bullet:
    BASE_SPEED = 400     # pixel/giây
    RADIUS = 6
    LIFETIME = 3.0       # giây tự hủy
    MAX_BOUNCE = 2       # số lần nảy tối đa (BounceModifier dùng)

    def __init__(self, x, y, target_x, target_y,
                 damage: float, rune_tree=None):
        self.x = float(x)
        self.y = float(y)
        self.radius = Bullet.RADIUS
        self.damage = damage
        self.rune_tree = rune_tree   # RuneTree | None
        self.alive = True
        self.elapsed = 0.0

        # Tính vector vận tốc hướng về target (normalize rồi nhân speed)
<<<<<<< HEAD
        dx   = target_x - float(x)
        dy   = target_y - float(y)
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * Bullet.BASE_SPEED
            self.vy = (dy / dist) * Bullet.BASE_SPEED
        else:
            self.vx = Bullet.BASE_SPEED
            self.vy = 0.0
=======
        # self.vx, self.vy = ...
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

        # State dùng bởi các Modifier
        self.spiral_angle = 0.0   # SpiralModifier xoay vận tốc mỗi frame
        self.bounce_count = 0     # BounceModifier đếm số lần đã nảy
        self.bounce_redirect = False  # BounceModifier set True để không bị kill ngay

        # Stack count — số lần cùng loại element được chọn
        # Dùng khi on_hit để nhân damage/duration
        self.element_stack = 1    # mặc định 1, RuneTree tính khi build

    def update(self, dt: float) -> None:
        # 1. Gọi rune_tree.on_update(self, dt) nếu có
        # 2. Di chuyển: self.x += self.vx * dt, self.y += self.vy * dt
        # 3. Cộng elapsed, nếu >= LIFETIME thì self.alive = False
<<<<<<< HEAD
        if self.rune_tree:
            self.rune_tree.on_update(self, dt)
        self.x       += self.vx * dt
        self.y       += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= Bullet.LIFETIME:
            self.alive = False
=======
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55

    def on_hit(self, enemy, context: dict) -> None:
        # 1. Reset bounce_redirect = False
        # 2. Gọi rune_tree.on_hit(self, enemy, context) nếu có
        # 3. Nếu bounce_redirect vẫn False → self.alive = False
<<<<<<< HEAD
        self.bounce_redirect = False
        if self.rune_tree:
            self.rune_tree.on_hit(self, enemy, context)
        if not self.bounce_redirect:
            self.alive = False

    def redirect(self, new_vx: float, new_vy: float) -> None:
        # BounceModifier gọi hàm này để đổi hướng đạn
        self.vx              = new_vx
        self.vy              = new_vy
        self.bounce_redirect = True  # giữ bullet sống sau on_hit
        self.elapsed         = 0.0   # reset lifetime
=======
        pass

    def redirect(self, new_vx: float, new_vy: float) -> None:
        # BounceModifier gọi hàm này để đổi hướng đạn
        # Set self.vx, self.vy mới
        # Set self.bounce_redirect = True (giữ bullet sống)
        # Reset self.elapsed = 0
        pass
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
