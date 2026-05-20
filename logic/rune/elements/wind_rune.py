import math
from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class WindRune(ElementRune):
    """
    Rune Gió — đẩy lui quái khi trúng đạn, gây slow nhẹ sau đó.
    Stack: chọn 2 lần → knockback mạnh hơn, slow lâu hơn.
    """
    KNOCKBACK_DIST = 120.0   # pixel đẩy ra
    SLOW_FACTOR    = 0.7     # quái còn 70% tốc độ
    SLOW_DURATION  = 2.0     # giây

    def on_hit(self, bullet, enemy, context: dict) -> None:
        # Knockback: đẩy quái ra xa theo hướng đạn bay
        dx   = enemy.x - bullet.x
        dy   = enemy.y - bullet.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            kx, ky = dx / dist, dy / dist
        else:
            # Quái trùng vị trí đạn → dùng hướng vận tốc đạn làm fallback
            spd = math.hypot(bullet.vx, bullet.vy)
            kx, ky = (bullet.vx / spd, bullet.vy / spd) if spd > 0 else (1, 0)
        kb = self.KNOCKBACK_DIST * bullet.element_stack
        enemy.x += kx * kb
        enemy.y += ky * kb

        # Slow nhẹ sau knockback
        slow = StatusEffect(
            effect_type='slow',
            damage_per_sec=0.0,
            duration=self.SLOW_DURATION * bullet.element_stack,
            slow_factor=self.SLOW_FACTOR,
        )
        enemy.add_status(slow)

    def get_display_name(self) -> str:
        return "Rune Gió"

    def get_description(self) -> str:
        return f"Đẩy lui {self.KNOCKBACK_DIST}px + slow {int((1-self.SLOW_FACTOR)*100)}%"

    def get_color(self) -> tuple:
        return (180, 230, 255)
