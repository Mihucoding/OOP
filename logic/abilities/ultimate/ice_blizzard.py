from logic.abilities.ultimate.ultimate_base import UltimateAbility
from logic.entities.status_effect import StatusEffect


class IceBlizzard(UltimateAbility):
    """Bão băng bán kính 240px — đóng băng + damage tất cả enemy."""
    COOLDOWN = 9.0
    RADIUS   = 240.0
    DAMAGE   = 25.0
    FREEZE_DURATION = 3.0

    @property
    def name(self): return "Ice Blizzard"
    @property
    def color(self): return (140, 200, 255)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
            # Stun = đóng băng hoàn toàn
            e.add_status(StatusEffect(
                'stun', 0.0, self.FREEZE_DURATION, slow_factor=0.0))
            e.add_status(StatusEffect(
                'chill', 0.0, self.FREEZE_DURATION, slow_factor=0.0))
