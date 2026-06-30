from logic.abilities.ultimate.ultimate_base import UltimateAbility


class ShadowNova(UltimateAbility):
    """Nova bóng tối — AoE damage thuần, không cần element."""
    COOLDOWN = 8.0
    RADIUS   = 180.0
    DAMAGE   = 50.0

    @property
    def name(self): return "Shadow Nova"
    @property
    def color(self): return (160, 80, 200)

    def _apply(self, player, targets, context):
        for e in targets:
            e.take_damage(self.DAMAGE)
