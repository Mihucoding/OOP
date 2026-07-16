import math
import random


class XPOrb:
    RADIUS         = 8
    COLLECT_RADIUS = 40    # tự thu khi player trong bán kính này
    MAGNET_RADIUS  = 180   # bắt đầu hút về phía player khi trong bán kính này
    MAGNET_SPEED   = 250   # tốc độ bay về phía player (pixel/s)
    # Ma sát văng lúc rơi (px/s²) — đủ mạnh để orb chỉ "nảy" ra một chút quanh
    # chỗ quái chết rồi dừng hẳn trong ~0.1-0.2s, KHÔNG trôi dạt xa (giá trị cũ
    # 4.0 quá yếu: ở tốc độ văng tối đa quãng đường trôi trước khi dừng lên tới
    # hàng ngàn pixel, orb trôi mất hút khỏi vị trí rơi).
    SCATTER_FRICTION = 900.0

    def __init__(self, x: float, y: float, value: int,
                 vx: float = 0.0, vy: float = 0.0):
        self.x      = float(x)
        self.y      = float(y)
        self.prev_x = self.x
        self.prev_y = self.y
        self.radius = XPOrb.RADIUS
        self.value  = value
        self.alive  = True
        self.is_magnetized = False
        # Vận tốc ban đầu (scatter effect)
        self.vx = vx
        self.vy = vy

    def update(self, dt: float, player_x: float, player_y: float,
               extra_magnet: float = 0.0) -> None:
        self.prev_x = self.x
        self.prev_y = self.y
        dist         = math.hypot(player_x - self.x, player_y - self.y)
        magnet_radius = self.MAGNET_RADIUS + extra_magnet
        self.is_magnetized = dist <= magnet_radius

        if self.is_magnetized:
            # Bay về phía player
            if dist > 0:
                self.x += (player_x - self.x) / dist * self.MAGNET_SPEED * dt
                self.y += (player_y - self.y) / dist * self.MAGNET_SPEED * dt
        else:
            # Giảm dần vận tốc scatter
            self.x  += self.vx * dt
            self.y  += self.vy * dt
            speed    = math.hypot(self.vx, self.vy)
            friction = self.SCATTER_FRICTION * dt
            if speed > friction:
                ratio   = (speed - friction) / speed
                self.vx *= ratio
                self.vy *= ratio
            else:
                self.vx = self.vy = 0.0

    def check_collect(self, player_x: float, player_y: float) -> bool:
        dist = math.hypot(player_x - self.x, player_y - self.y)
        if dist <= self.COLLECT_RADIUS:
            self.alive = False
            return True
        return False


def scatter_xp(cx: float, cy: float, total_value: int,
               count: int = 4) -> list:
    """Tạo nhiều XPOrb nhỏ toả ra xung quanh vị trí (cx, cy)."""
    orbs  = []
    value = max(1, total_value // count)
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(40, 120)
        vx    = math.cos(angle) * speed
        vy    = math.sin(angle) * speed
        orbs.append(XPOrb(cx, cy, value, vx, vy))
    return orbs
