from logic.rune.rune_component import ElementRune
from logic.entities.status_effect import StatusEffect


class BloodRune(ElementRune):
    """
    Rune Máu — gây chảy máu (hemorrhage) khi trúng.
    Stack: mỗi stack tăng damage/s thêm HEMORRHAGE_DPS.
    Visual: Blood Mage VFX3 (ball bay) + VFX2 (impact nổ).
    """

    HEMORRHAGE_DPS = 6.0    # damage/giây mỗi stack
    HEMORRHAGE_DUR = 5.0    # giây

    def on_hit(self, bullet, enemy, context: dict) -> None:
        stack = getattr(bullet, 'element_stack', 1)
        dps   = self.HEMORRHAGE_DPS * stack
        enemy.add_status(StatusEffect(
            'burn', dps, self.HEMORRHAGE_DUR))   # dùng lại type 'burn'

    def get_display_name(self) -> str: return "Rune Máu"
    def get_description(self)  -> str:
        return f"Chảy máu {self.HEMORRHAGE_DPS} HP/s trong {self.HEMORRHAGE_DUR}s"
    def get_color(self)        -> tuple: return (180, 0, 50)
