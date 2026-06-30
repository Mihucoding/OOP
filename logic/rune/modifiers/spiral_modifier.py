import math
from logic.rune.rune_component import ModifierRune


class SpiralModifier(ModifierRune):
    """
    Rune Xoắn Ốc — quay vận tốc đạn mỗi frame.
    Stack: chọn 2 lần → ROTATE_SPEED nhân đôi.
    """
    ROTATE_SPEED = 180.0   # độ/giây

    def __init__(self):
        super().__init__()
        self.stack = 1   # tăng khi player chọn lại

    def on_update(self, bullet, dt: float) -> None:
        # Xoay vector vận tốc một góc nhỏ mỗi frame
        angle_rad = math.radians(self.ROTATE_SPEED * self.stack * dt)
        cos_a     = math.cos(angle_rad)
        sin_a     = math.sin(angle_rad)
        vx_new    = bullet.vx * cos_a - bullet.vy * sin_a
        vy_new    = bullet.vx * sin_a + bullet.vy * cos_a
        bullet.vx = vx_new
        bullet.vy = vy_new

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Spiral Rune"
    def get_description(self) -> str: return "Bullets fly in a spiral path"
    def get_color(self) -> tuple: return (200, 150, 255)
