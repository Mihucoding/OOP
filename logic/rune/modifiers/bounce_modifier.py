import math
from logic.rune.rune_component import ModifierRune

class BounceModifier(ModifierRune):
    """
    Rune Nảy — đạn trúng quái rồi nảy sang quái gần nhất.
    Stack: chọn 2 lần → bounce_max tăng thêm MAX_BOUNCE.
    """
    MAX_BOUNCE = 2
    BOUNCE_SPEED = 420.0
    POINT_COST = 2   # nhân rộng sát thương qua nhiều địch — mạnh, tốn điểm hơn

    def on_hit(self, bullet, enemy, context: dict) -> None:
        bounce_max = self.MAX_BOUNCE * self.stack
        if bullet.bounce_count >= bounce_max:
            return

        # Tìm quái còn sống gần nhất (không phải quái vừa trúng, dist > 0)
        nearest      = None
        nearest_dist = float('inf')
        for e in context.get('enemies', []):
            if e is enemy or not e.alive:
                continue
            d = math.hypot(e.x - bullet.x, e.y - bullet.y)
            if d > 0 and d < nearest_dist:   # bỏ qua enemy trùng vị trí bullet
                nearest_dist = d
                nearest      = e

        if nearest is not None:
            dx   = nearest.x - bullet.x
            dy   = nearest.y - bullet.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                bullet.redirect(
                    (dx / dist) * self.BOUNCE_SPEED,
                    (dy / dist) * self.BOUNCE_SPEED,
                )
                bullet.bounce_count += 1

    def on_update(self, bullet, dt: float, context: dict = None) -> None:
        # Sau khi redirect, bullet.bounce_redirect = True → game loop không kill
        # Sau 1 frame, bounce_redirect được reset trong bullet.on_hit
        pass

    def on_fire(self, bullet, context: dict) -> list:
        return []

    def get_display_name(self) -> str: return "Bounce Rune"
    def get_description(self) -> str:
        return f"Bullets bounce up to {self.MAX_BOUNCE} times (Cost: {self.POINT_COST})"
    def get_color(self) -> tuple: return (255, 220, 50)
