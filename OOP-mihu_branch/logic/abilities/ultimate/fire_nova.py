import math
from logic.abilities.ultimate.ultimate_base import UltimateAbility
from logic.entities.status_effect import StatusEffect


class FireNova(UltimateAbility):
    """Vòng lửa nổ bán kính 220px — burn tất cả + đẩy ra ngoài."""
    COOLDOWN  = 8.0
    RADIUS    = 220.0
    DAMAGE    = 40.0
    PUSHBACK  = 160.0   # px knockback

    @property
    def name(self): return "Fire Nova"
    @property
    def color(self): return (255, 100, 20)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            e.add_status(StatusEffect('burn', damage_per_sec=12.0, duration=4.0))
            # Đẩy ra xa tâm player
            dx = e.x - player.x
            dy = e.y - player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                e.x += (dx / dist) * self.PUSHBACK
                e.y += (dy / dist) * self.PUSHBACK
