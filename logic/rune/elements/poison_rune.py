from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class PoisonRune(ElementRune):
    """
    Rune Độc — rút máu từ từ.
    Stack: chọn 2 lần → poison_damage nhân đôi.
    """
    POISON_DAMAGE = 5.0     # HP/giây
    POISON_DURATION = 5.0

    def on_hit(self, bullet, enemy, context: dict) -> None:
<<<<<<< HEAD
        poison = StatusEffect(
            effect_type='poison',
            damage_per_sec=self.POISON_DAMAGE * bullet.element_stack,
            duration=self.POISON_DURATION,
        )
        enemy.add_status(poison)

    def get_display_name(self) -> str: return "Poison Rune"
    def get_description(self) -> str:
        return f"Poisons for {self.POISON_DAMAGE} HP/s over {self.POISON_DURATION}s"
=======
        # Tạo StatusEffect loại 'poison'
        # damage_per_sec = POISON_DAMAGE * bullet.element_stack
        # duration = POISON_DURATION
        pass

    def get_display_name(self) -> str: return "Rune Độc"
    def get_description(self) -> str:
        return f"Độc {self.POISON_DAMAGE} HP/s trong {self.POISON_DURATION}s"
>>>>>>> 3e15ae77a0ed8863193acdf98696434a388c7c55
    def get_color(self) -> tuple: return (120, 255, 80)
