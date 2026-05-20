import math
from logic.rune.rune_component import ModifierRune


class SplitModifier(ModifierRune):
    """
    Rune Tách — khi bắn tạo thêm 2 viên đạn lệch ±SPLIT_ANGLE độ.
    Stack: chọn 2 lần → tạo thêm 4 viên thay vì 2.
    """
    SPLIT_ANGLE = 20.0   # độ lệch mỗi bên

    def __init__(self):
        super().__init__()
        self.stack = 1

    def on_fire(self, bullet, context: dict) -> list:
        from logic.entities.bullet import Bullet
        new_bullets  = []
        base_angle   = math.atan2(bullet.vy, bullet.vx)

        # Mỗi stack tạo thêm 1 cặp ±SPLIT_ANGLE*i
        for i in range(1, self.stack + 1):
            for sign in (1, -1):
                angle = base_angle + math.radians(self.SPLIT_ANGLE * i * sign)
                # Tạo đạn mới tại cùng vị trí, hướng xoay góc angle
                b = Bullet(
                    bullet.x,
                    bullet.y,
                    bullet.x + math.cos(angle) * 100,
                    bullet.y + math.sin(angle) * 100,
                    bullet.damage,
                    bullet.rune_tree,
                )
                b.element_stack  = bullet.element_stack
                b.bounce_count   = bullet.bounce_count
                new_bullets.append(b)
        return new_bullets

    def on_update(self, bullet, dt: float) -> None:
        pass

    def get_display_name(self) -> str: return "Rune Tách"
    def get_description(self) -> str: return "Bắn tạo thêm 2 viên đạn"
    def get_color(self) -> tuple: return (255, 180, 100)
