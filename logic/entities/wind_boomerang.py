import math


class WindBoomerang:
    """
    Đạn gió dạng boomerang — bay ra tầm cố định rồi quay về player.
    Xuyên qua địch (pierce), mỗi địch chỉ bị đánh 1 lần mỗi chiều.
    """
    SPEED        = 380.0    # pixel/giây — tốc độ bay đi
    RETURN_SPEED = 680.0    # pixel/giây — rút về NHANH hơn hẳn lúc bay đi
    MAX_RANGE    = 550.0    # pixel trước khi quay đầu (nếu bay xa hơn điểm nhắm)
    PAUSE_TIME   = 0.08     # giây khựng lại tại điểm xa nhất trước khi rút về
    CATCH_RADIUS = 30.0     # pixel từ player để "bắt" và biến mất
    RADIUS       = 10       # bán kính va chạm
    MAX_LIFE     = 6.0      # giây tự hủy (safety)
    SPIN_SPEED   = 1920.0   # độ/giây — tốc độ xoay hình ảnh boomerang
    CAN_ORBIT    = False    # boomerang có quỹ đạo ra/về riêng — KHÔNG ép orbit
                            # (Self-Centered trên cây gió chỉ +count/+duration)

    def __init__(self, x: float, y: float,
                 target_x: float, target_y: float,
                 damage: float, rune_tree=None):
        self.x           = float(x)
        self.y           = float(y)
        self.damage      = damage
        self.rune_tree   = rune_tree
        self.alive       = True
        self.elapsed     = 0.0
        self.radius      = self.RADIUS
        self.visual_type = 'wind_boomerang'
        self.is_crit     = False
        self.pierce      = True   # báo cho collision handler không break

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * self.SPEED
            self.vy = (dy / dist) * self.SPEED
        else:
            self.vx = self.SPEED
            self.vy = 0.0

        # Dừng tại điểm nhắm (nếu gần) hoặc hết tầm (nếu nhắm xa hơn MAX_RANGE)
        self._target_dist = min(dist, self.MAX_RANGE) if dist > 0 else self.MAX_RANGE

        self.phase         = 'out'   # 'out' | 'pause' | 'return'
        self.dist_traveled = 0.0
        self._pause_timer  = 0.0
        self._hit_ids: set[int] = set()   # địch đã trúng trong trip này

        # Cập nhật mỗi frame từ game_loop
        self.player_x = float(x)
        self.player_y = float(y)

        # Góc xoay boomerang cho renderer
        self.spin_angle = 0.0   # degrees, tăng liên tục

        # Tương thích với rune_tree.on_hit / on_update interface
        self.element_stack   = 1
        self.bounce_count    = 0   # HitAndRunModifier: số lần đã phản xạ khỏi tường (game_loop tự đếm)
        self.spiral_angle    = 0.0

    def update(self, dt: float, context: dict = None) -> None:
        # Modifier chỉnh quỹ đạo (Spiral làm cong đường bay lúc ra + lúc về).
        # Rune dựa-trên-quãng-đường (VD FuriousOutburstModifier) cần tính CẢ
        # chặng về mới đủ quãng đường round-trip (~640px) như boomerang thật.
        if self.rune_tree is not None:
            self.rune_tree.on_update(self, dt, context)

        if self.phase == 'out':
            step = math.hypot(self.vx * dt, self.vy * dt)
            self.dist_traveled += step
            if self.dist_traveled >= self._target_dist:
                # Tới điểm nhắm/hết tầm → khựng lại thật ngắn trước khi rút về
                self.phase        = 'pause'
                self._pause_timer = self.PAUSE_TIME
                self.vx = 0.0
                self.vy = 0.0
        elif self.phase == 'pause':
            self.vx = 0.0
            self.vy = 0.0
            self._pause_timer -= dt
            if self._pause_timer <= 0:
                self.phase = 'return'
                self._hit_ids.clear()   # có thể trúng lại trên đường về
                self._point_to_player()
        elif self.phase == 'return':
            dx = self.player_x - self.x
            dy = self.player_y - self.y
            d  = math.hypot(dx, dy)
            if d <= self.CATCH_RADIUS:
                self.alive = False
                return
            # Track player liên tục — rút về NHANH hơn lúc bay đi
            self.vx = (dx / d) * self.RETURN_SPEED
            self.vy = (dy / d) * self.RETURN_SPEED

        self.x          += self.vx * dt
        self.y          += self.vy * dt
        self.spin_angle  = (self.spin_angle + self.SPIN_SPEED * dt) % 360.0
        self.elapsed    += dt
        if self.elapsed >= self.MAX_LIFE:
            self.alive = False

    def on_hit(self, enemy, context: dict) -> bool:
        """Trả về False nếu enemy này đã trúng trong trip hiện tại (không damage lại)."""
        if id(enemy) in self._hit_ids:
            return False
        self._hit_ids.add(id(enemy))
        if self.rune_tree:
            self.rune_tree.on_hit(self, enemy, context)
        # Boomerang giữ alive sau khi trúng
        return True

    def redirect(self, new_vx: float, new_vy: float) -> None:
        # game_loop gọi khi boomerang phản xạ khỏi tường (HitAndRunModifier),
        # CHỈ ở pha 'out' (xem game_loop._update_bullet_wall_bounce): đổi
        # hướng bay + reset quãng đường đã đi, như phóng phát mới từ đó.
        self.vx            = new_vx
        self.vy            = new_vy
        self.dist_traveled = 0.0

    def _point_to_player(self) -> None:
        dx = self.player_x - self.x
        dy = self.player_y - self.y
        d  = math.hypot(dx, dy)
        if d > 0:
            self.vx = (dx / d) * self.RETURN_SPEED
            self.vy = (dy / d) * self.RETURN_SPEED
