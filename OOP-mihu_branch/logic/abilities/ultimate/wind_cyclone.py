import math
from logic.abilities.ultimate.ultimate_base import UltimateAbility
from logic.entities.status_effect import StatusEffect


class WindCyclone(UltimateAbility):
    """Lốc xoáy — hút enemy vào tâm rồi knockback ra ngoài mạnh."""
    COOLDOWN   = 8.0
    RADIUS     = 250.0
    DAMAGE     = 30.0
    PULL_DIST  = 80.0    # hút vào
    PUSH_DIST  = 220.0   # đẩy ra

    @property
    def name(self): return "Wind Cyclone"
    @property
    def color(self): return (160, 230, 160)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            dx = e.x - player.x
            dy = e.y - player.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                nx, ny = dx / dist, dy / dist
                # Hút vào trước
                e.x = player.x + nx * max(0, dist - self.PULL_DIST)
                e.y = player.y + ny * max(0, dist - self.PULL_DIST)
                # Rồi đẩy ra
                e.x += nx * self.PUSH_DIST
                e.y += ny * self.PUSH_DIST
            e.add_status(StatusEffect('slow', 0.0, 3.0, slow_factor=0.4))
