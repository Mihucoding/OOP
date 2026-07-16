import math

from logic.rune.rune_tree import RuneTree

class Bullet:
    RADIUS       = 6
    BASE_SPEED   = 400.0
    LIFETIME     = 2.0
    CAN_ORBIT = True     # cho phép Self-Centered/Flash biến thành vệ tinh quay

    def __init__(self, x, y, target_x, target_y, damage: float, rune_tree=None):
        """
        Khởi tạo viên đạn.
        - Tính toán vector vận tốc (vx, vy) hướng về (target_x, target_y).
        - Lưu trữ `rune_tree` của chiêu thức đã bắn ra viên đạn này.

        👉 BƯỚC TIẾP THEO (Bước 12): Mở file [logic/rune/rune_tree.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/rune/rune_tree.py) đọc hàm `on_fire` để xem cách viên đạn bị nhân bản (ngọc Split).
        """
        self.x = float(x)
        self.y = float(y)
        self.radius = Bullet.RADIUS
        self.damage = float(damage)

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * Bullet.BASE_SPEED
            self.vy = (dy / dist) * Bullet.BASE_SPEED
        else:
            self.vx = Bullet.BASE_SPEED
            self.vy = 0.0

        self.alive   = True
        self.elapsed = 0.0

        self.rune_tree = rune_tree or RuneTree()

        # State dùng bởi các Modifier
        self.bounce_count    = 0     # HitAndRunModifier: số lần đã phản xạ khỏi tường
        self.pierce_remaining = 0    # PiercingEyesModifier: số địch còn xuyên được
        self._hit_ids: set[int] = set()   # địch đã tính damage — tránh ăn damage lặp
                                           # nhiều frame liền khi đạn xuyên còn dính hitbox

        # Stack count — số lần cùng loại element được chọn. Dùng khi on_hit để
        # nhân damage/duration.
        self.element_stack = 1

    def update(self, dt: float, context: dict | None = None) -> None:
        """
        Cập nhật vị trí đạn mỗi frame.
        - Gọi `rune_tree.on_update(self, dt, context)` để ngọc bổ trợ thay đổi đường bay/tốc độ.
        - Di chuyển đạn theo vận tốc hiện tại (vx, vy).
        - Cộng elapsed, hết LIFETIME thì tự huỷ.

        👉 BƯỚC TIẾP THEO (Bước 14): Quay lại [logic/rune/rune_tree.py](file:///c:/Users/acer/Downloads/OOP-mihu_branch/logic/rune/rune_tree.py) và xem hàm `on_update` hoạt động thế nào.
        """
        if not self.alive:
            return

        if context is None:
            context = {}

        self.rune_tree.on_update(self, dt, context)

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.elapsed += dt
        if self.elapsed >= self.LIFETIME:
            self.alive = False

    def on_hit(self, enemy, context: dict):
        """
        Gọi khi đạn chạm địch.
        - Bỏ qua nếu địch này đã tính damage trong lượt xuyên hiện tại.
        - Gọi `rune_tree.on_hit(self, enemy, context)` để Element/Modifier áp hiệu ứng.
        - Bounce vừa redirect hướng → giữ đạn sống, không tiêu lượt xuyên.
        - Còn pierce_remaining → xuyên qua (giữ sống, trừ 1 lượt xuyên).
        - Hết pierce/bounce → tự huỷ.
        """
        if id(enemy) in self._hit_ids:
            return False
        self.bounce_redirect = False
        self.rune_tree.on_hit(self, enemy, context)
        if self.bounce_redirect:
            return None
        if self.pierce_remaining > 0:
            self.pierce_remaining -= 1
            self._hit_ids.add(id(enemy))
            return None
        self.alive = False

    def redirect(self, new_vx: float, new_vy: float) -> None:
        """HitAndRunModifier gọi hàm này (qua game_loop) để đổi hướng đạn khi
        phản xạ khỏi tường — reset elapsed để range/duration tính lại từ đầu."""
        self.vx              = new_vx
        self.vy              = new_vy
        self.bounce_redirect = True   # giữ bullet sống nếu gọi từ trong on_hit
        self.elapsed         = 0.0
