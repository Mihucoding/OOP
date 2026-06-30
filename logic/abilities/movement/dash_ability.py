"""
DashAbility — lao nhanh theo hướng di chuyển.

Kiến trúc mở rộng: tất cả movement ability kế thừa MovementAbility.
"""
import math


class MovementAbility:
    """Base class cho mọi khả năng di chuyển đặc biệt."""
    COOLDOWN = 3.0
    NAME     = "Move"
    COLOR    = (180, 180, 255)

    def __init__(self):
        self.timer = 0.0   # giây còn lại (> 0 → đang hồi)

    def tick(self, dt: float) -> None:
        self.timer = max(0.0, self.timer - dt)

    def is_ready(self) -> bool:
        return self.timer <= 0.0

    def activate(self, player, move_x: float, move_y: float) -> None:
        """Kích hoạt ability. Override trong subclass."""

    def reset(self) -> None:
        self.timer = self.COOLDOWN

    @property
    def cooldown_ratio(self) -> float:
        """0.0 = sẵn sàng, 1.0 = vừa dùng xong."""
        return min(1.0, self.timer / self.COOLDOWN)


class DashAbility(MovementAbility):
    """
    Dash — lao 200px theo hướng di chuyển (hoặc hướng nhìn nếu đứng yên).
    Cooldown 3s.
    """
    COOLDOWN   = 3.0
    DASH_DIST  = 180.0
    DASH_TIME  = 0.18
    NAME       = "Dash"
    COLOR      = (100, 200, 255)

    def activate(self, player, move_x: float, move_y: float) -> None:
        if not self.is_ready():
            return
        length = math.hypot(move_x, move_y)
        if length > 0:
            nx = move_x / length
            ny = move_y / length
        else:
            # Nếu đứng yên → dash sang phải mặc định
            nx, ny = float(getattr(player, "facing_dir", 1)), 0.0

        player.dash_timer = self.DASH_TIME
        player.dash_duration = self.DASH_TIME
        player.dash_vel_x = nx * (self.DASH_DIST / self.DASH_TIME)
        player.dash_vel_y = ny * (self.DASH_DIST / self.DASH_TIME)
        player.vel_x = player.dash_vel_x
        player.vel_y = player.dash_vel_y
        player.last_dash_dir_x = nx
        player.last_dash_dir_y = ny
        player.last_dash_forward = nx == 0 or nx * getattr(player, "facing_dir", 1) >= 0
        self.reset()
