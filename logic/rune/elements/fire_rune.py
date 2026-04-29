from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class FireRune(ElementRune):
    """
    Rune Lửa — đốt cháy quái khi trúng đạn.
    Stack: chọn 2 lần → burn_damage nhân đôi.
    """

    BURN_DAMAGE = 8.0    # damage/giây
    BURN_DURATION = 3.0  # giây

    def on_hit(self, bullet, enemy, context: dict) -> None:
        burn = StatusEffect(
            effect_type="burn",
            damage_per_sec=self.BURN_DAMAGE * bullet.element_stack,
            duration=self.BURN_DURATION,
        )
        enemy.add_status(burn)

    def get_display_name(self) -> str:
        return "Rune Lửa"

    def get_description(self) -> str:
        return f"Đốt cháy {self.BURN_DAMAGE} HP/s trong {self.BURN_DURATION}s"

    def get_color(self) -> tuple:
        return (255, 100, 30)
