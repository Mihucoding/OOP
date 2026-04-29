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
        # Tạo thêm (2 * self.stack) viên đạn mới:
        # Mỗi cặp lệch ±SPLIT_ANGLE * i so với hướng gốc
        # Clone bullet (vị trí giống, rune_tree giống, chỉ đổi vx/vy)
        # Trả về list[Bullet] mới
        pass

    def on_update(self, bullet, dt: float) -> None:
        pass

    def get_display_name(self) -> str: return "Rune Tách"
    def get_description(self) -> str: return "Bắn tạo thêm 2 viên đạn"
    def get_color(self) -> tuple: return (255, 180, 100)
