import math


class Bullet:
    BASE_SPEED = 400     # pixel/giây
    RADIUS = 6
    LIFETIME = 3.0       # giây tự hủy
    MAX_BOUNCE = 2       # số lần nảy tối đa (BounceModifier dùng)
    CAN_ORBIT = True     # cho phép Self-Centered/Flash biến thành vệ tinh quay

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
        dx   = target_x - float(x)
        dy   = target_y - float(y)
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * Bullet.BASE_SPEED
            self.vy = (dy / dist) * Bullet.BASE_SPEED
        else:
            self.vx = Bullet.BASE_SPEED
            self.vy = 0.0

        # State dùng bởi các Modifier
        self.spiral_angle = 0.0   # TwistOfFateModifier xoay vận tốc mỗi frame
        self.bounce_count = 0     # BounceModifier đếm số lần đã nảy
        self.bounce_redirect = False  # BounceModifier set True để không bị kill ngay
        self.pierce_remaining = 0     # PiercingEyesModifier: số địch còn xuyên được
        self._hit_ids: set[int] = set()  # địch đã tính damage — tránh ăn damage lặp
                                          # nhiều frame liền khi đạn xuyên còn dính hitbox

        # Stack count — số lần cùng loại element được chọn
        # Dùng khi on_hit để nhân damage/duration
        self.element_stack = 1    # mặc định 1, RuneTree tính khi build

    def update(self, dt: float, context: dict = None) -> None:
        # 1. Gọi rune_tree.on_update(self, dt, context) nếu có
        # 2. Di chuyển: self.x += self.vx * dt, self.y += self.vy * dt
        # 3. Cộng elapsed, nếu >= LIFETIME thì self.alive = False
        if self.rune_tree:
            self.rune_tree.on_update(self, dt, context)
        self.x       += self.vx * dt
        self.y       += self.vy * dt
        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.alive = False

    def on_hit(self, enemy, context: dict):
        # 1. Bỏ qua nếu địch này đã tính damage trong lượt xuyên hiện tại
        # 2. Reset bounce_redirect = False, gọi rune_tree.on_hit(...)
        # 3. Nếu Bounce vừa redirect → giữ sống, không tiêu pierce
        # 4. Còn pierce_remaining → xuyên qua (giữ sống, trừ 1 lượt xuyên)
        # 5. Hết pierce/bounce → self.alive = False
        if id(enemy) in self._hit_ids:
            return False
        self.bounce_redirect = False
        if self.rune_tree:
            self.rune_tree.on_hit(self, enemy, context)
        if self.bounce_redirect:
            return None
        if self.pierce_remaining > 0:
            self.pierce_remaining -= 1
            self._hit_ids.add(id(enemy))
            return None
        self.alive = False

    def redirect(self, new_vx: float, new_vy: float) -> None:
        # BounceModifier gọi hàm này để đổi hướng đạn
        self.vx              = new_vx
        self.vy              = new_vy
        self.bounce_redirect = True  # giữ bullet sống sau on_hit
        self.elapsed         = 0.0   # reset lifetime
