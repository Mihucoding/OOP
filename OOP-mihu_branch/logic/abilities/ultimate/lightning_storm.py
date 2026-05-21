from logic.abilities.ultimate.ultimate_base import UltimateAbility


class LightningStorm(UltimateAbility):
    """Sét dây chuyền — stun + 60 damage tối đa 6 enemy."""
    COOLDOWN     = 7.0
    RADIUS       = 200.0
    DAMAGE       = 60.0
    MAX_TARGETS  = 6
    STUN_DUR     = 1.2

    @property
    def name(self): return "Thunder Chain"
    @property
    def color(self): return (200, 180, 255)

    def _apply(self, player, targets, context):
        hit = targets[:self.MAX_TARGETS]
        for e in hit:
            e.take_damage(self.DAMAGE)
            e.cast_lock_timer = max(getattr(e, 'cast_lock_timer', 0.0), self.STUN_DUR)
            context.get('effects', []).append({
                'kind': 'lightning_ultimate',
                'x': e.x,
                'y': e.y,
                'duration': 0.35,
            })
