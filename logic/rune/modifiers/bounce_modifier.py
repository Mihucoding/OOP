import math
from logic.rune.rune_component import ModifierRune


class BounceModifier(ModifierRune):
    """
    Rune Nảy — đạn trúng quái rồi nảy sang quái gần nhất.
    Stack: chọn 2 lần → bounce_max tăng thêm MAX_BOUNCE.
    """
    MAX_BOUNCE = 2
    BOUNCE_SPEED = 420.0

    def __init__(self):
        super().__init__()
        self.stack = 1

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # 1. Tính bounce_max = MAX_BOUNCE * self.stack
        # 2. Nếu bullet.bounce_count < bounce_max:
        #    a. Tìm quái gần nhất trong context['enemies'] (trừ enemy vừa trúng)
        #    b. Nếu tìm thấy: bullet.redirect(vx, vy về quái đó)
        #       bullet.bounce_count += 1
        #    c. Nếu không tìm thấy: không làm gì (bullet tự chết)
        pass

    def on_update(self, bullet, dt: float) -> None:
        # Sau khi redirect, bullet.bounce_redirect = True → game loop không kill
        # Sau 1 frame, bounce_redirect được reset trong bullet.on_hit
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Rune Nảy"
    def get_description(self) -> str: return f"Đạn nảy tối đa {self.MAX_BOUNCE} lần"
    def get_color(self) -> tuple: return (255, 220, 50)
